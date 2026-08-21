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
      version: 1,
      onCreate: (db, version) async {
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
      },
    );
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
}