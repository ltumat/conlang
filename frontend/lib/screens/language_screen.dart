import 'package:flutter/material.dart';
import 'package:conlang/screens/wlist_screen.dart';

class LanguageScreen extends StatelessWidget {
  final String language;

  const LanguageScreen({super.key, required this.language});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(language),
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
              onPressed: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (context) => WordsScreen(language: language),
                  ),
                );
              },
              icon: const Icon(Icons.list),
              label: const Text('Vocabulary List'),
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
