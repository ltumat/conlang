import 'package:flutter/material.dart';
import 'package:conlang/screens/add_word_screen.dart';
import 'package:conlang/screens/word_screen.dart';
import 'package:conlang/services/api_service.dart';

class WordsScreen extends StatefulWidget {
  final String language;

  const WordsScreen({super.key, required this.language});

  @override
  State<WordsScreen> createState() => _WordsScreenState();
}

class _WordsScreenState extends State<WordsScreen> {
  final ApiService _apiService = ApiService();
  late Future<List<Map<String, dynamic>>> _wordsFuture;
  final TextEditingController _searchController = TextEditingController();
  String _search = '';

  @override
  void initState() {
    super.initState();
    _wordsFuture = _apiService.fetchWords(widget.language);
    _searchController.addListener(() {
      setState(() => _search = _searchController.text.trim().toLowerCase());
    });
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  Future<void> _addWord() async {
    await Navigator.push<Map<String, String>>(
      context,
      MaterialPageRoute(
        builder: (context) => AddWordScreen(language: widget.language),
      ),
    );
    setState(() => _wordsFuture = _apiService.fetchWords(widget.language));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('French'),
        actions: [
          IconButton(
            tooltip: 'Add word',
            onPressed: _addWord,
            icon: const Icon(Icons.add),
          ),
        ],
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

          final words = (snapshot.data ?? [])
              .where((word) => (word['word'] as String? ?? '')
                  .toLowerCase()
                  .contains(_search))
              .toList();
          return Column(
            children: [
              Padding(
                padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
                child: TextField(
                  controller: _searchController,
                  decoration: InputDecoration(
                    labelText: 'Search words',
                    prefixIcon: const Icon(Icons.search),
                    suffixIcon: _search.isEmpty
                        ? null
                        : IconButton(
                            tooltip: 'Clear search',
                            onPressed: _searchController.clear,
                            icon: const Icon(Icons.clear),
                          ),
                    border: const OutlineInputBorder(),
                  ),
                ),
              ),
              Expanded(
                child: words.isEmpty
                    ? const Center(child: Text('No matching words.'))
                    : ListView.separated(
                        padding: const EdgeInsets.all(16),
                        itemCount: words.length,
                        separatorBuilder: (_, __) => const SizedBox(height: 8),
                        itemBuilder: (context, index) {
                          final word = words[index];
                          return Card(
                            child: ListTile(
                              contentPadding: const EdgeInsets.symmetric(
                                horizontal: 20,
                                vertical: 8,
                              ),
                              title: Text(
                                word['word'] as String? ?? 'Unknown word',
                                style: Theme.of(context).textTheme.titleLarge,
                              ),
                              subtitle: Text(
                                word['pronunciation'] == null
                                    ? 'Pronunciation unavailable'
                                    : '/${word['pronunciation']}/',
                              ),
                              trailing: const Icon(Icons.chevron_right),
                              onTap: () => Navigator.push(
                                context,
                                MaterialPageRoute(
                                  builder: (context) => WordScreen(word: word),
                                ),
                              ),
                            ),
                          );
                        },
                      ),
              ),
            ],
          );
        },
      ),
    );
  }
}
