import 'package:flutter/material.dart';
import 'package:conlang/screens/wlist_screen.dart';
import 'package:conlang/services/local_database.dart';

class LanguageScreen extends StatefulWidget {
  final String language;

  const LanguageScreen({super.key, required this.language});

  @override
  State<LanguageScreen> createState() => _LanguageScreenState();
}

class _LanguageScreenState extends State<LanguageScreen> {
  int _savedCount = 0;

  @override
  void initState() {
    super.initState();
    _loadSavedCount();
  }

  Future<void> _loadSavedCount() async {
    final count = await LocalDatabase.getSavedWordCount(widget.language);
    if (mounted) {
      setState(() => _savedCount = count);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.language),
      ),
      body: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const SizedBox(height: 24),
            FilledButton.icon(
              onPressed: () {
                // TODO: navigate to training session
              },
              icon: const Icon(Icons.school),
              label: const Text('Start Training'),
              style: FilledButton.styleFrom(
                padding: const EdgeInsets.symmetric(vertical: 20),
                textStyle: const TextStyle(fontSize: 18),
              ),
            ),
            const SizedBox(height: 16),
            OutlinedButton.icon(
              onPressed: () async {
                await Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (context) => WordsScreen(language: widget.language),
                  ),
                );
                _loadSavedCount();
              },
              icon: const Icon(Icons.list),
              label: const Text('Vocabulary List'),
              style: OutlinedButton.styleFrom(
                padding: const EdgeInsets.symmetric(vertical: 20),
                textStyle: const TextStyle(fontSize: 18),
              ),
            ),
            const SizedBox(height: 16),
            OutlinedButton.icon(
              onPressed: () async {
                await Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (context) => WordsScreen(language: widget.language),
                  ),
                );
                _loadSavedCount();
              },
              icon: Icon(_savedCount > 0 ? Icons.bookmark : Icons.bookmark_border),
              label: Text(
                _savedCount > 0
                    ? 'Saved Words ($_savedCount)'
                    : 'Saved Words',
              ),
              style: OutlinedButton.styleFrom(
                padding: const EdgeInsets.symmetric(vertical: 20),
                textStyle: const TextStyle(fontSize: 18),
              ),
            ),
          ],
        ),
      ),
    );
  }
}