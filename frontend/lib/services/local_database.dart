import 'dart:convert';

import 'package:conlang/services/srs.dart';
import 'package:sqflite/sqflite.dart';

class LocalDatabase {
  static Database? _db;

  static Future<Database> get database async {
    if (_db != null) return _db!;
    _db = await _init();
    return _db!;
  }

  static Future<Database> _init() async {
    final dbPath = await getDatabasesPath();
    final path = '$dbPath/conlang.db';
    return openDatabase(
      path,
      version: 4,
      onCreate: (db, version) async {
        await _createTables(db);
      },
      onUpgrade: (db, oldVersion, newVersion) async {
        // All CREATE statements are idempotent (IF NOT EXISTS), so old
        // databases whose recorded version lags behind their actual schema
        // (e.g. from a pre-migration install) are repaired safely.
        await _createTables(db);
        await _addPracticeColumnIfNeeded(db);
      },
    );
  }

  static Future<void> _createWordProgressTable(Database db) async {
    await db.execute('''
      CREATE TABLE IF NOT EXISTS word_progress (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        word TEXT NOT NULL,
        language TEXT NOT NULL,
        ease_factor REAL NOT NULL DEFAULT 2.5,
        repetitions INTEGER NOT NULL DEFAULT 0,
        interval_days REAL NOT NULL DEFAULT 0,
        due_at TEXT,
        last_reviewed_at TEXT,
        last_practiced_at TEXT,
        UNIQUE(word, language)
      )
    ''');
  }

  /// Add the practice-tracking column to word_progress tables created
  /// before it existed (v3 -> v4). Does not touch the SM-2 columns.
  static Future<void> _addPracticeColumnIfNeeded(Database db) async {
    final cols = await db.rawQuery('PRAGMA table_info(word_progress)');
    if (cols.isEmpty) return; // table doesn't exist yet; created with column
    final names = cols.map((c) => c['name'] as String).toSet();
    if (!names.contains('last_practiced_at')) {
      await db.execute(
        'ALTER TABLE word_progress ADD COLUMN last_practiced_at TEXT',
      );
    }
  }

  static Future<void> _createTables(Database db) async {
    await db.execute('''
      CREATE TABLE IF NOT EXISTS saved_words (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        word TEXT NOT NULL,
        language TEXT NOT NULL,
        data TEXT NOT NULL,
        saved_at TEXT NOT NULL,
        UNIQUE(word, language)
      )
    ''');
    await db.execute('''
      CREATE TABLE IF NOT EXISTS search_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        word TEXT NOT NULL,
        language TEXT NOT NULL,
        viewed_at TEXT NOT NULL,
        UNIQUE(word, language)
      )
    ''');
    await db.execute('''
      CREATE TABLE IF NOT EXISTS app_settings (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
      )
    ''');
    await _createWordProgressTable(db);
  }

  /// Save a word to local storage. Returns true if inserted, false if already saved.
  static Future<bool> saveWord(
      Map<String, dynamic> word, String language) async {
    final db = await database;
    final wordStr = word['word'] as String;
    final savedAt = DateTime.now().toIso8601String();

    try {
      await db.insert(
        'saved_words',
        {
          'word': wordStr,
          'language': language,
          'data': jsonEncode(word),
          'saved_at': savedAt,
        },
        conflictAlgorithm: ConflictAlgorithm.ignore,
      );
      return true;
    } catch (_) {
      return false;
    }
  }

  /// Remove a saved word. Returns true if removed.
  static Future<bool> removeWord(String word, String language) async {
    final db = await database;
    final count = await db.delete(
      'saved_words',
      where: 'word = ? AND language = ?',
      whereArgs: [word, language],
    );
    return count > 0;
  }

  /// Check if a word is saved.
  static Future<bool> isWordSaved(String word, String language) async {
    final db = await database;
    final result = await db.query(
      'saved_words',
      where: 'word = ? AND language = ?',
      whereArgs: [word, language],
      limit: 1,
    );
    return result.isNotEmpty;
  }

  /// Get saved words for a language, optionally matching a search query (client-side filter).
  static Future<List<Map<String, dynamic>>> getSavedWords(
    String language, {
    String query = '',
  }) async {
    final db = await database;
    final rows = await db.query(
      'saved_words',
      where: 'language = ?',
      whereArgs: [language],
      orderBy: 'word ASC',
    );
    var words = rows
        .map((row) =>
            Map<String, dynamic>.from(jsonDecode(row['data'] as String)))
        .toList();
    if (query.isNotEmpty) {
      final q = query.toLowerCase();
      words = words.where((w) {
        final word = (w['word'] as String? ?? '').toLowerCase();
        return word.contains(q);
      }).toList();
    }
    return words;
  }

  /// Get all saved languages (languages that have at least one saved word).
  static Future<List<String>> getSavedLanguages() async {
    final db = await database;
    final rows = await db.rawQuery(
      'SELECT DISTINCT language FROM saved_words ORDER BY language',
    );
    return rows.map((r) => r['language'] as String).toList();
  }

  /// Get count of saved words for a language.
  static Future<int> getSavedWordCount(String language) async {
    final db = await database;
    final result = await db.rawQuery(
      'SELECT COUNT(*) AS cnt FROM saved_words WHERE language = ?',
      [language],
    );
    return Sqflite.firstIntValue(result) ?? 0;
  }

  static Future<void> ensureTable() async {
    final db = await database;
    // Idempotent repair for databases whose recorded version lags behind
    // their actual schema.
    await db.execute('''
      CREATE TABLE IF NOT EXISTS search_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        word TEXT NOT NULL,
        language TEXT NOT NULL,
        viewed_at TEXT NOT NULL,
        UNIQUE(word, language)
      )
    ''');
  }

  static Future<void> ensureProgressTable() async {
    final db = await database;
    await _createWordProgressTable(db);
    await _addPracticeColumnIfNeeded(db);
  }

  static Future<void> _ensureSettingsTable() async {
    final db = await database;
    await db.execute('''
      CREATE TABLE IF NOT EXISTS app_settings (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
      )
    ''');
  }

  // -----------------------------------------------------------------------
  // App settings (simple key-value store)
  // -----------------------------------------------------------------------

  static const _defaultSessionSize = 20;
  static const _sessionSizeRange = (min: 5, max: 50);

  /// Number of words per training session (due + practice fill combined).
  static Future<int> getSessionSize() async {
    await _ensureSettingsTable();
    final db = await database;
    final rows = await db.query(
      'app_settings',
      where: 'key = ?',
      whereArgs: ['session_size'],
      limit: 1,
    );
    final value = int.tryParse(rows.firstOrNull?['value'] as String? ?? '');
    if (value == null) return _defaultSessionSize;
    return value.clamp(_sessionSizeRange.min, _sessionSizeRange.max);
  }

  static Future<void> setSessionSize(int size) async {
    await _ensureSettingsTable();
    final db = await database;
    final clamped = size.clamp(_sessionSizeRange.min, _sessionSizeRange.max);
    await db.insert(
      'app_settings',
      {'key': 'session_size', 'value': clamped.toString()},
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
  }

  /// Add a word to search history (most recent first, max 10 per language).
  static Future<void> addSearchHistory(String word, String language) async {
    await ensureTable();
    final db = await database;
    final now = DateTime.now().toIso8601String();

    await db.insert(
      'search_history',
      {
        'word': word,
        'language': language,
        'viewed_at': now,
      },
      conflictAlgorithm: ConflictAlgorithm.replace,
    );

    // Keep only the 10 most recent entries for this language
    final all = await db.query(
      'search_history',
      where: 'language = ?',
      whereArgs: [language],
      orderBy: 'viewed_at DESC',
    );
    if (all.length > 10) {
      final idsToKeep = all.take(10).map((r) => r['id']).toList();
      await db.delete(
        'search_history',
        where:
            'language = ? AND id NOT IN (${idsToKeep.map((_) => '?').join(',')})',
        whereArgs: [language, ...idsToKeep],
      );
    }
  }

  /// Get search history for a language (most recent first, max 10).
  static Future<List<String>> getSearchHistory(String language) async {
    await ensureTable();
    final db = await database;
    final rows = await db.query(
      'search_history',
      where: 'language = ?',
      whereArgs: [language],
      orderBy: 'viewed_at DESC',
      limit: 10,
    );
    return rows.map((r) => r['word'] as String).toList();
  }

  // -----------------------------------------------------------------------
  // Spaced repetition (SM-2)
  // -----------------------------------------------------------------------

  /// Words that are due for review right now, plus words never trained yet.
  ///
  /// Overdue words come first (most overdue at the top), then new words.
  static Future<List<Map<String, dynamic>>> getDueWords(
    String language, {
    int limit = 20,
  }) async {
    await ensureProgressTable();
    final db = await database;
    final now = DateTime.now().toIso8601String();
    final rows = await db.rawQuery(
      '''
      SELECT s.data AS data
      FROM saved_words s
      LEFT JOIN word_progress p
        ON s.word = p.word AND s.language = p.language
      WHERE s.language = ?
        AND (p.word IS NULL OR p.due_at IS NULL OR p.due_at <= ?)
      ORDER BY
        CASE WHEN p.word IS NULL THEN 1 ELSE 0 END,
        p.due_at ASC,
        s.word ASC
      LIMIT ?
      ''',
      [language, now, limit],
    );
    return rows
        .map((row) =>
            Map<String, dynamic>.from(jsonDecode(row['data'] as String)))
        .toList();
  }

  /// Number of words currently due for review (including new, untrained words).
  static Future<int> getDueWordCount(String language) async {
    await ensureProgressTable();
    final db = await database;
    final now = DateTime.now().toIso8601String();
    final result = await db.rawQuery(
      '''
      SELECT COUNT(*) AS cnt
      FROM saved_words s
      LEFT JOIN word_progress p
        ON s.word = p.word AND s.language = p.language
      WHERE s.language = ?
        AND (p.word IS NULL OR p.due_at IS NULL OR p.due_at <= ?)
      ''',
      [language, now],
    );
    return Sqflite.firstIntValue(result) ?? 0;
  }

  /// Number of words that are scheduled but not yet due.
  static Future<int> getScheduledWordCount(String language) async {
    await ensureProgressTable();
    final db = await database;
    final now = DateTime.now().toIso8601String();
    final result = await db.rawQuery(
      '''
      SELECT COUNT(*) AS cnt
      FROM saved_words s
      JOIN word_progress p
        ON s.word = p.word AND s.language = p.language
      WHERE s.language = ? AND p.due_at > ?
      ''',
      [language, now],
    );
    return Sqflite.firstIntValue(result) ?? 0;
  }

  /// Words that are already scheduled but NOT due yet, hardest first.
  ///
  /// Used for practice sessions when nothing is due: "hardest" means the
  /// lowest ease factor, then fewest successful repetitions. Words practiced
  /// least recently come first among equally hard words. The returned words
  /// keep their original schedule — practice reviews never reschedule them.
  static Future<List<Map<String, dynamic>>> getHardestWords(
    String language, {
    int limit = 20,
  }) async {
    await ensureProgressTable();
    final db = await database;
    final now = DateTime.now().toIso8601String();
    final rows = await db.rawQuery(
      '''
      SELECT s.data AS data
      FROM saved_words s
      JOIN word_progress p
        ON s.word = p.word AND s.language = p.language
      WHERE s.language = ? AND p.due_at > ?
      ORDER BY
        p.ease_factor ASC,
        p.repetitions ASC,
        COALESCE(p.last_practiced_at, '') ASC,
        s.word ASC
      LIMIT ?
      ''',
      [language, now, limit],
    );
    return rows
        .map((row) =>
            Map<String, dynamic>.from(jsonDecode(row['data'] as String)))
        .toList();
  }

  /// Apply a review rating to a word and update its SM-2 schedule.
  static Future<void> reviewWord(
    String word,
    String language,
    Rating rating,
  ) async {
    await ensureProgressTable();
    final db = await database;
    final now = DateTime.now();

    final existing = await db.query(
      'word_progress',
      where: 'word = ? AND language = ?',
      whereArgs: [word, language],
      limit: 1,
    );

    final row = existing.isNotEmpty ? existing.first : null;
    final state = ReviewState(
      easeFactor: (row?['ease_factor'] as num?)?.toDouble() ?? 2.5,
      repetitions: row?['repetitions'] as int? ?? 0,
      intervalDays: (row?['interval_days'] as num?)?.toDouble() ?? 0,
    );

    final result = scheduleReview(state, rating, now);

    await db.insert(
      'word_progress',
      {
        'word': word,
        'language': language,
        'ease_factor': result.state.easeFactor,
        'repetitions': result.state.repetitions,
        'interval_days': result.state.intervalDays,
        'due_at': result.dueAt.toIso8601String(),
        'last_reviewed_at': now.toIso8601String(),
      },
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
  }

  /// Record a practice review WITHOUT touching the SM-2 schedule.
  ///
  /// Practice is voluntary extra training (used when nothing is due), so the
  /// word's due date, ease factor, repetitions and interval stay exactly as
  /// they are — it still comes due at its originally scheduled time, where
  /// the next real review will apply the full SM-2 logic.
  static Future<void> practiceWord(
    String word,
    String language,
    Rating rating,
  ) async {
    await ensureProgressTable();
    final db = await database;

    final updated = await db.update(
      'word_progress',
      {
        'last_practiced_at': DateTime.now().toIso8601String(),
      },
      where: 'word = ? AND language = ?',
      whereArgs: [word, language],
    );

    if (updated == 0) {
      // No progress row yet (word was never really reviewed): create a
      // placeholder without scheduling it. due_at stays NULL so it remains
      // part of the normal due queue.
      await db.insert(
        'word_progress',
        {
          'word': word,
          'language': language,
          'last_practiced_at': DateTime.now().toIso8601String(),
        },
        conflictAlgorithm: ConflictAlgorithm.ignore,
      );
    }
  }
}
