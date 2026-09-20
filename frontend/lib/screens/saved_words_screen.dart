import 'package:flutter/material.dart';
import 'package:conlang/screens/word_screen.dart';
import 'package:conlang/services/local_database.dart';

/// Screen showing saved words with search and client-side pagination.
class SavedWordsScreen extends StatefulWidget {
  final String language;

  const SavedWordsScreen({super.key, required this.language});

  @override
  State<SavedWordsScreen> createState() => _SavedWordsScreenState();
}

class _SavedWordsScreenState extends State<SavedWordsScreen> {
  final TextEditingController _searchController = TextEditingController();
  final FocusNode _searchFocus = FocusNode();

  /// All saved words matching the current query (loaded from DB).
  List<Map<String, dynamic>> _allWords = [];

  /// Currently visible slice.
  final List<Map<String, dynamic>> _visible = [];
  static const int _pageSize = 10;
  int _loadedCount = 0;
  bool _loading = true;
  String _query = '';

  @override
  void initState() {
    super.initState();
    _searchController.addListener(_onSearchChanged);
    _loadWords();
  }

  @override
  void dispose() {
    _searchController.removeListener(_onSearchChanged);
    _searchController.dispose();
    _searchFocus.dispose();
    super.dispose();
  }

  Future<void> _loadWords() async {
    setState(() => _loading = true);
    final words = await LocalDatabase.getSavedWords(
      widget.language,
      query: _query,
    );
    if (!mounted) return;
    setState(() {
      _allWords = words;
      _loadedCount = 0;
      _visible.clear();
      _addPage();
      _loading = false;
    });
  }

  void _onSearchChanged() {
    final text = _searchController.text.trim().toLowerCase();
    if (text == _query) return;
    setState(() => _query = text);
    _loadWords();
  }

  void _addPage() {
    final end = (_loadedCount + _pageSize < _allWords.length)
        ? _loadedCount + _pageSize
        : _allWords.length;
    for (int i = _loadedCount; i < end; i++) {
      _visible.add(_allWords[i]);
    }
    _loadedCount = end;
  }

  void _loadMore() => setState(_addPage);

  bool get _hasMore => _loadedCount < _allWords.length;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(title: Text('Saved Words — ${widget.language}')),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
            child: TextField(
              controller: _searchController,
              focusNode: _searchFocus,
              decoration: InputDecoration(
                hintText: 'Search saved words…',
                prefixIcon: const Icon(Icons.search),
                suffixIcon: _query.isEmpty
                    ? null
                    : IconButton(
                        tooltip: 'Clear',
                        onPressed: () {
                          _searchController.clear();
                          _searchFocus.unfocus();
                        },
                        icon: const Icon(Icons.clear),
                      ),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(28),
                  borderSide: BorderSide.none,
                ),
                filled: true,
                fillColor: theme.colorScheme.surfaceContainerHighest.withValues(alpha: 0.5),
              ),
            ),
          ),
          Expanded(child: _buildContent(theme)),
        ],
      ),
    );
  }

  Widget _buildContent(ThemeData theme) {
    if (_loading) {
      return const Center(child: CircularProgressIndicator());
    }

    if (_allWords.isEmpty) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.bookmark_border, size: 48,
                color: theme.colorScheme.onSurfaceVariant.withValues(alpha: 0.4)),
            const SizedBox(height: 12),
            Text(
              _query.isEmpty
                  ? 'No saved words yet.\nTap + on a word to save it.'
                  : 'No saved words matching "$_query"',
              style: theme.textTheme.bodyLarge?.copyWith(
                color: theme.colorScheme.onSurfaceVariant,
              ),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      );
    }

    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
          child: Row(
            children: [
              Text(
                '${_visible.length} of ${_allWords.length}',
                style: theme.textTheme.bodySmall?.copyWith(
                  color: theme.colorScheme.onSurfaceVariant,
                ),
              ),
            ],
          ),
        ),
        Expanded(
          child: ListView.separated(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            itemCount: _visible.length + (_hasMore ? 1 : 0),
            separatorBuilder: (_, __) => const SizedBox(height: 6),
            itemBuilder: (context, index) {
              if (index == _visible.length) {
                return Padding(
                  padding: const EdgeInsets.symmetric(vertical: 8),
                  child: Center(
                    child: OutlinedButton.icon(
                      onPressed: _loadMore,
                      icon: const Icon(Icons.expand_more, size: 18),
                      label: const Text('Load more'),
                    ),
                  ),
                );
              }

              final word = _visible[index];
              return Card(
                child: ListTile(
                  contentPadding: const EdgeInsets.symmetric(
                    horizontal: 20,
                    vertical: 8,
                  ),
                  title: Text(
                    word['word'] as String? ?? 'Unknown',
                    style: theme.textTheme.titleLarge,
                  ),
                  subtitle: Text(
                    word['pronunciation'] == null
                        ? ''
                        : '/${word['pronunciation']}/',
                  ),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () => Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (_) => WordScreen(
                        word: word,
                        language: widget.language,
                      ),
                    ),
                  ),
                ),
              );
            },
          ),
        ),
      ],
    );
  }
}