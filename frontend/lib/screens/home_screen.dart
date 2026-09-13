import 'package:flutter/material.dart';
import 'package:conlang/services/api_service.dart';
import 'package:conlang/widgets/activity_tile.dart';
import 'package:conlang/widgets/language_tile.dart';
import 'package:conlang/widgets/profile_tile.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final ApiService _apiService = ApiService();
  late Future<List<Map<String, dynamic>>> _languagesFuture;

  @override
  void initState() {
    super.initState();
    _languagesFuture = _apiService.fetchLanguages();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Conlang')),
      body: FutureBuilder<List<Map<String, dynamic>>>(
        future: _languagesFuture,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }
          final languages = snapshot.data ?? [];
          final langMap = {for (final l in languages) l['name'] as String: l};

          final french = langMap['French'];
          final wordCount = (french?['word_count'] as num?)?.toInt() ?? 0;

          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              SizedBox(
                height: 200,
                child: LanguageTile(name: 'French', wordCount: wordCount),
              ),
              const SizedBox(height: 16),
              const SizedBox(
                height: 200,
                child: ActivityTile(
                  streakDays: 3,
                  recentWords: [5, 8, 0, 12, 6, 3, 9],
                ),
              ),
              const SizedBox(height: 16),
              const SizedBox(
                height: 200,
                child: ProfileTile(),
              ),
            ],
          );
        },
      ),
    );
  }
}