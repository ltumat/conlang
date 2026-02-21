import 'package:flutter/material.dart';
import 'package:conlang/services/api_service.dart';

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
      appBar: AppBar(
        title: const Text('Conlang'),
      ),
      body: FutureBuilder<List<Map<String, dynamic>>>(
        future: _languagesFuture,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }

          if (snapshot.hasError) {
            return Center(child: Text('Error: ${snapshot.error}'));
          }

          final languages = snapshot.data!;
          return ListView.builder(
            itemCount: languages.length,
            itemBuilder: (context, index) {
              final lang = languages[index];
              return ListTile(
                title: Text(lang['name']),
                subtitle: Text(
                  '${lang['word_count']} words · ${lang['video_count']} videos',
                ),
                trailing: const Icon(Icons.chevron_right),
                onTap: () {
                  // TODO: navigate to language detail
                },
              );
            },
          );
        },
      ),
    );
  }
}
