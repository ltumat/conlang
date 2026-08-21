import 'package:flutter/material.dart';
import 'package:conlang/screens/add_word_screen.dart';
import 'package:conlang/screens/word_screen.dart';
import 'package:conlang/services/api_service.dart';
import 'package:conlang/services/local_database.dart';

class WordsScreen extends StatefulWidget {
  final String language;

  const WordsScreen({super.key, required this.language});

  @override
  State<WordsScreen> createState() => _WordsScreenState();
}

class _WordsScreenState extends State<WordsScreen> {
  final ApiService _apiService = ApiService();
  final TextEditingController _searchController = TextEditingController();
  String _search = '';

  /// false = all words (from API), true = saved words (local DB)
  bool _showSaved = false;

  /// Future for the currently active tab
  late Future<List<Map<String, dynamic>>> _wordsFuture;

  @override
  void initState() {
    super.initState();
    _wordsFuture = _fetchWords();
    _searchController.addListener(() {
      setState(() => _search = _searchController.text.trim().toLowerCase());
    });
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  Future<List<Map<String, dynamic>>> _fetchWords() {
    if (_showSaved) {
      return LocalDatabase.getSavedWords(widget.language);
    } else {
      return _apiService.fetchWords(widget.language);
    }
  }

  void _switchTab(bool showSaved) {
    if (showSaved == _showSaved) return;
    setState(() {
      _showSaved = showSaved;
      _wordsFuture = _fetchWords();
      _search = '';
      _searchController.clear();
    });
  }

  Future<void> _addWord() async {
    await Navigator.push<Map<String, String>>(
      context,
      MaterialPageRoute(
        builder: (context) => AddWordScreen(language: widget.language),
      ),
    );
    setState(() => _wordsFuture = _fetchWords());
  }

  Future<void> _refresh() {
    setState(() => _wordsFuture = _fetchWords());
    return _wordsFuture;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.language),
        actions: [
          if (!_showSaved)
            IconButton(
              tooltip: 'Add word',
              onPressed: _addWord,
              icon: const Icon(Icons.add),
            ),
        ],
      ),
      body: Column(
        children: [
          // Tab toggle: All / Saved
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 0),
            child: SegmentedButton<bool>(
              segments: const [
                ButtonSegment(value: false, label: Text('All'), icon: Icon(Icons.list)),
                ButtonSegment(
                  value: true,
                  label: Text('Saved'),
                  icon: Icon(Icons.bookmark),
                ),
              ],
              selected: {_showSaved},
              onSelectionChanged: (selected) => _switchTab(selected.first),
            ),
          ),
          // Search bar (only for "All" tab)
          if (!_showSaved)
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
          // Word list
          Expanded(
            child: FutureBuilder<List<Map<String, dynamic>>>(
              future: _wordsFuture,
              builder: (context, snapshot) {
                if (snapshot.connectionState == ConnectionState.waiting) {
                  return const Center(child: CircularProgressIndicator());
                }
                if (snapshot.hasError) {
                  return Center(
                    child: Padding(
                      padding: const EdgeInsets.all(24),
                      child: Text(
                        'Error: ${snapshot.error}',
                        textAlign: TextAlign.center,
                      ),
                    ),
                  );
                }

                final words = (snapshot.data ?? [])
                    .where((word) => _showSaved || (word['word'] as String? ?? '')
                        .toLowerCase()
                        .contains(_search))
                    .toList();

                if (words.isEmpty) {
                  return Center(
                    child: Text(
                      _showSaved
                          ? 'No saved words yet.\nTap the bookmark icon on a word to save it.'
                          : 'No matching words.',
                      textAlign: TextAlign.center,
                    ),
                  );
                }

                return RefreshIndicator(
                  onRefresh: _refresh,
                  child: ListView.separated(
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
                          trailing: _showSaved
                              ? IconButton(
                                  tooltip: 'Remove from saved',
                                  icon: const Icon(Icons.bookmark_remove),
                                  onPressed: () async {
                                    await LocalDatabase.removeWord(
                                      word['word'] as String,
                                      widget.language,
                                    );
                                    _refresh();
                                  },
                                )
                              : const Icon(Icons.chevron_right),
                          onTap: () => Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (context) => WordScreen(
                                word: word,
                                language: widget.language,
                              ),
                            ),
                          ),
                        ),
                      );
                    },
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}