import 'package:flutter/material.dart';
import 'package:conlang/services/api_service.dart';
import 'package:conlang/screens/add_word_screen.dart';

class WordsScreen extends StatefulWidget {
  final String language;

  const WordsScreen({super.key, required this.language});

  @override
  State<WordsScreen> createState() => _WordsScreenState();
}

class _WordsScreenState extends State<WordsScreen> {
  final ApiService _apiService = ApiService();
  late Future<List<Map<String, dynamic>>> _wordsFuture;

  @override
  void initState() {
    super.initState();
    _wordsFuture = _apiService.fetchWords(widget.language);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.language),
      ),
      body: FutureBuilder<List<Map<String, dynamic>>>(
        future: _wordsFuture,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }

          if (snapshot.hasError) {
            return Center(child: Text('Error: ${snapshot.error}'));
          }

          final words = snapshot.data!;
          if (words.isEmpty) {
            return const Center(child: Text('No words yet.'));
          }

          return ListView.builder(
            itemCount: words.length,
            itemBuilder: (context, index) {
              final word = words[index];
              return ListTile(
                title: Text(word['word']),
                subtitle: Text(word['translation']),
              );
            },
          );
        },
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () async {
          final result = await Navigator.push<Map<String, String>>(
            context,
            MaterialPageRoute(
              builder: (context) => AddWordScreen(language: widget.language),
            ),
          );
          if (result != null) {
            // Refresh the word list after adding
            setState(() {
              _wordsFuture = _apiService.fetchWords(widget.language);
            });
          }
        },
        child: const Icon(Icons.add),
      ),
    );
  }
}
