import 'dart:convert';

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
      version: 2,
      onCreate: (db, version) async {
        await _createTables(db);
      },
      onUpgrade: (db, oldVersion, newVersion) async {
        if (oldVersion < 2) {
          await db.execute('''
            CREATE TABLE search_history (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              word TEXT NOT NULL,
              language TEXT NOT NULL,
              viewed_at TEXT NOT NULL,
              UNIQUE(word, language)
            )
          ''');
        }
      },
    );
  }

  static Future<void> _createTables(Database db) async {
    await db.execute('''
      CREATE TABLE saved_words (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        word TEXT NOT NULL,
        language TEXT NOT NULL,
        data TEXT NOT NULL,
        saved_at TEXT NOT NULL,
        UNIQUE(word, language)
      )
    ''');
    await db.execute('''
      CREATE TABLE search_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        word TEXT NOT NULL,
        language TEXT NOT NULL,
        viewed_at TEXT NOT NULL,
        UNIQUE(word, language)
      )
    ''');
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

  /// Get all saved words for a language.
  static Future<List<Map<String, dynamic>>> getSavedWords(
      String language) async {
    final db = await database;
    final rows = await db.query(
      'saved_words',
      where: 'language = ?',
      whereArgs: [language],
      orderBy: 'word ASC',
    );
    return rows
        .map((row) => Map<String, dynamic>.from(jsonDecode(row['data'] as String)))
        .toList();
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
    // Check if search_history exists; create it if not (handles stale DBs).
    final tables = await db.rawQuery(
      "SELECT name FROM sqlite_master WHERE type='table' AND name='search_history'",
    );
    if (tables.isEmpty) {
      await db.execute('''
        CREATE TABLE search_history (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          word TEXT NOT NULL,
          language TEXT NOT NULL,
          viewed_at TEXT NOT NULL,
          UNIQUE(word, language)
        )
      ''');
      // Bump the internal version so version 2 tables stay known
      await db.execute('PRAGMA user_version = 2');
    }
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
        where: 'language = ? AND id NOT IN (${idsToKeep.map((_) => '?').join(',')})',
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
}