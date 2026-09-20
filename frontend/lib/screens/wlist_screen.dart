import 'package:flutter/material.dart';
import 'package:conlang/screens/word_screen.dart';
import 'package:conlang/services/api_service.dart';
import 'package:conlang/services/local_database.dart';

/// Dictionary screen with search-as-you-type, pagination, and persisted history.
class WordsScreen extends StatefulWidget {
  final String language;

  const WordsScreen({super.key, required this.language});

  @override
  State<WordsScreen> createState() => _WordsScreenState();
}

class _WordsScreenState extends State<WordsScreen> {
  final ApiService _apiService = ApiService();
  final TextEditingController _searchController = TextEditingController();
  final FocusNode _searchFocus = FocusNode();

  String _query = '';

  final List<Map<String, dynamic>> _results = [];
  int _total = 0;
  int _offset = 0;
  static const int _limit = 10;
  bool _loading = false;
  bool _hasMore = false;

  /// Persisted history of clicked words (most recent first).
  List<String> _history = [];

  @override
  void initState() {
    super.initState();
    _searchController.addListener(_onSearchChanged);
    _loadHistory();
  }

  @override
  void dispose() {
    _searchController.removeListener(_onSearchChanged);
    _searchController.dispose();
    _searchFocus.dispose();
    super.dispose();
  }

  Future<void> _loadHistory() async {
    final h = await LocalDatabase.getSearchHistory(widget.language);
    if (mounted) setState(() => _history = h);
  }

  void _onSearchChanged() {
    final text = _searchController.text.trim();
    if (text.toLowerCase() == _query) return;
    setState(() => _query = text.toLowerCase());
    if (_query.isNotEmpty) {
      _search(_query);
    } else {
      _clearResults();
    }
  }

  Future<void> _search(String query) async {
    setState(() {
      _loading = true;
      _results.clear();
      _offset = 0;
    });
    try {
      final data = await _apiService.searchWords(
        widget.language,
        query: query,
        limit: _limit,
        offset: 0,
      );
      final words = (data['words'] as List<dynamic>)
          .map((w) => Map<String, dynamic>.from(w as Map))
          .toList();
      final total = data['total'] as int;
      setState(() {
        _results.addAll(words);
        _total = total;
        _offset = words.length;
        _hasMore = _offset < _total;
        _loading = false;
      });
    } catch (e) {
      setState(() => _loading = false);
    }
  }

  Future<void> _loadMore() async {
    if (_loading || !_hasMore) return;
    setState(() => _loading = true);
    try {
      final data = await _apiService.searchWords(
        widget.language,
        query: _query,
        limit: _limit,
        offset: _offset,
      );
      final words = (data['words'] as List<dynamic>)
          .map((w) => Map<String, dynamic>.from(w as Map))
          .toList();
      final total = data['total'] as int;
      setState(() {
        _results.addAll(words);
        _total = total;
        _offset += words.length;
        _hasMore = _offset < _total;
        _loading = false;
      });
    } catch (e) {
      setState(() => _loading = false);
    }
  }

  void _clearResults() {
    setState(() {
      _results.clear();
      _total = 0;
      _offset = 0;
      _hasMore = false;
    });
  }

  Future<void> _saveWordToHistory(String word) async {
    await LocalDatabase.addSearchHistory(word, widget.language);
    // Refresh history from DB
    final h = await LocalDatabase.getSearchHistory(widget.language);
    if (mounted) setState(() => _history = h);
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(title: Text('Dictionary — ${widget.language}')),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
            child: TextField(
              controller: _searchController,
              focusNode: _searchFocus,
              autofocus: true,
              decoration: InputDecoration(
                hintText: 'Search the dictionary…',
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
    if (_query.isEmpty) {
      return _buildHistory(theme);
    }

    if (_loading && _results.isEmpty) {
      return const Center(child: CircularProgressIndicator());
    }

    if (_results.isEmpty && !_loading) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.search_off, size: 48,
                color: theme.colorScheme.onSurfaceVariant),
            const SizedBox(height: 12),
            Text('No results for "$_query"',
                style: theme.textTheme.bodyLarge),
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
                '${_results.length} of $_total results',
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
            itemCount: _results.length + (_hasMore ? 1 : 0),
            separatorBuilder: (_, __) => const SizedBox(height: 6),
            itemBuilder: (context, index) {
              if (index == _results.length) {
                return Padding(
                  padding: const EdgeInsets.symmetric(vertical: 8),
                  child: Center(
                    child: OutlinedButton.icon(
                      onPressed: _loading ? null : _loadMore,
                      icon: _loading
                          ? const SizedBox(
                              width: 16,
                              height: 16,
                              child: CircularProgressIndicator(strokeWidth: 2),
                            )
                          : const Icon(Icons.expand_more, size: 18),
                      label: Text(_loading ? 'Loading…' : 'Load more'),
                    ),
                  ),
                );
              }

              final word = _results[index];
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
                  onTap: () {
                    final wordText = word['word'] as String? ?? '';
                    _saveWordToHistory(wordText);
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (_) => WordScreen(
                          word: word,
                          language: widget.language,
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
    );
  }

  Widget _buildHistory(ThemeData theme) {
    if (_history.isEmpty) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.search, size: 48,
                color: theme.colorScheme.onSurfaceVariant.withValues(alpha: 0.4)),
            const SizedBox(height: 12),
            Text(
              'Search for a word above',
              style: theme.textTheme.bodyLarge?.copyWith(
                color: theme.colorScheme.onSurfaceVariant,
              ),
            ),
          ],
        ),
      );
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 8, 16, 8),
          child: Text('History',
              style: theme.textTheme.labelLarge?.copyWith(
                color: theme.colorScheme.onSurfaceVariant,
              )),
        ),
        Expanded(
          child: ListView.builder(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            itemCount: _history.length,
            itemBuilder: (_, i) {
              final word = _history[i];
              return Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: Card(
                  elevation: 0,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(10),
                    side: BorderSide(
                      color: theme.colorScheme.outlineVariant,
                    ),
                  ),
                  child: InkWell(
                    borderRadius: BorderRadius.circular(10),
                    onTap: () async {
                      try {
                        final wordData = await _apiService.fetchWord(
                          word,
                          widget.language,
                        );
                        if (!mounted) return;
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (_) => WordScreen(
                              word: wordData,
                              language: widget.language,
                            ),
                          ),
                        );
                      } catch (_) {
                        if (!mounted) return;
                        ScaffoldMessenger.of(context).showSnackBar(
                          SnackBar(content: Text('"$word" not found')),
                        );
                      }
                    },
                    child: Padding(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 14,
                        vertical: 12,
                      ),
                      child: Row(
                        children: [
                          Icon(Icons.history,
                              size: 18,
                              color: theme.colorScheme.onSurfaceVariant),
                          const SizedBox(width: 12),
                          Text(word,
                              style: theme.textTheme.bodyMedium?.copyWith(
                                fontWeight: FontWeight.w500,
                              )),
                          const Spacer(),
                          Icon(Icons.chevron_right,
                              size: 16,
                              color: theme.colorScheme.onSurfaceVariant),
                        ],
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