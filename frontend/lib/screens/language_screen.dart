import 'package:flutter/material.dart';
import 'package:conlang/screens/saved_words_screen.dart';
import 'package:conlang/screens/training_screen.dart';
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
  int _dueCount = 0;
  int _sessionSize = 20;

  @override
  void initState() {
    super.initState();
    _loadCounts();
    _loadSessionSize();
  }

  Future<void> _loadCounts() async {
    final count = await LocalDatabase.getSavedWordCount(widget.language);
    final due = await LocalDatabase.getDueWordCount(widget.language);
    if (mounted) {
      setState(() {
        _savedCount = count;
        _dueCount = due;
      });
    }
  }

  Future<void> _loadSessionSize() async {
    final size = await LocalDatabase.getSessionSize();
    if (mounted) setState(() => _sessionSize = size);
  }

  Future<void> _chooseSessionSize() async {
    final saved = await showDialog<int>(
      context: context,
      builder: (dialogContext) =>
          _TrainingOptionsDialog(initialSize: _sessionSize),
    );
    if (saved == null || saved == _sessionSize) return;
    await LocalDatabase.setSessionSize(saved);
    _loadSessionSize();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.language),
        actions: [
          IconButton(
            tooltip: 'Training options',
            icon: const Icon(Icons.tune),
            onPressed: _chooseSessionSize,
          ),
        ],
      ),
      body: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const SizedBox(height: 16),
            FilledButton.icon(
              onPressed: () async {
                await Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (context) =>
                        TrainingScreen(language: widget.language),
                  ),
                );
                _loadCounts();
              },
              icon: const Icon(Icons.school),
              label: Text(
                _dueCount > 0
                    ? 'Start Training ($_dueCount due)'
                    : 'Start Training',
              ),
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
                    builder: (context) =>
                        WordsScreen(language: widget.language),
                  ),
                );
                _loadCounts();
              },
              icon: const Icon(Icons.menu_book),
              label: const Text('Dictionary'),
              style: OutlinedButton.styleFrom(
                padding: const EdgeInsets.symmetric(vertical: 20),
                textStyle: const TextStyle(fontSize: 18),
              ),
            ),
            const SizedBox(height: 16),
            OutlinedButton.icon(
              onPressed: () {
                // TODO: navigate to conversation training
              },
              icon: const Icon(Icons.forum),
              label: const Text('Conversation Training'),
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
                    builder: (context) =>
                        SavedWordsScreen(language: widget.language),
                  ),
                );
                _loadCounts();
              },
              icon: Icon(
                  _savedCount > 0 ? Icons.bookmark : Icons.bookmark_border),
              label: Text(
                _savedCount > 0 ? 'Saved Words ($_savedCount)' : 'Saved Words',
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

class _TrainingOptionsDialog extends StatefulWidget {
  final int initialSize;

  static const _minSize = 5;
  static const _maxSize = 50;

  const _TrainingOptionsDialog({required this.initialSize});

  @override
  State<_TrainingOptionsDialog> createState() => _TrainingOptionsDialogState();
}

class _TrainingOptionsDialogState extends State<_TrainingOptionsDialog> {
  late int _size = widget.initialSize;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return AlertDialog(
      title: const Text('Training options'),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text('Session size', style: theme.textTheme.titleSmall),
          Text(
            '$_size words',
            style: theme.textTheme.headlineSmall,
          ),
          Slider(
            value: _size.toDouble().clamp(
                  _TrainingOptionsDialog._minSize.toDouble(),
                  _TrainingOptionsDialog._maxSize.toDouble(),
                ),
            min: _TrainingOptionsDialog._minSize.toDouble(),
            max: _TrainingOptionsDialog._maxSize.toDouble(),
            divisions: _TrainingOptionsDialog._maxSize -
                _TrainingOptionsDialog._minSize,
            label: '$_size',
            onChanged: (value) => setState(() => _size = value.round()),
          ),
          Text(
            'Due words come first; the rest is filled with practice of your '
            'hardest words.',
            style: theme.textTheme.bodySmall?.copyWith(
              color: theme.colorScheme.onSurfaceVariant,
            ),
          ),
        ],
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: const Text('Cancel'),
        ),
        FilledButton(
          onPressed: () => Navigator.pop(context, _size),
          child: const Text('Save'),
        ),
      ],
    );
  }
}
