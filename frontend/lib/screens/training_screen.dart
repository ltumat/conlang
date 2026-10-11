import 'package:flutter/material.dart';
import 'package:conlang/services/local_database.dart';
import 'package:conlang/services/srs.dart';

/// A spaced-repetition flashcard session for a language.
///
/// Words that are due (or new) are shown one by one. The user reveals the
/// meaning and grades their recall (Again / Hard / Good / Easy), which updates
/// the word's SM-2 schedule. Words rated "Again" re-enter the session queue.
class TrainingScreen extends StatefulWidget {
  final String language;

  const TrainingScreen({super.key, required this.language});

  @override
  State<TrainingScreen> createState() => _TrainingScreenState();
}

class _TrainingScreenState extends State<TrainingScreen> {
  /// Number of words in this session (due + practice fill combined).
  /// Loaded from the persisted user setting before each session.
  int _sessionSize = 20;

  /// One entry in the session queue: the word plus whether it's a real,
  /// scheduled review (updates the SM-2 schedule) or a practice review
  /// (extra training of hard words; never touches the schedule).
  late List<({Map<String, dynamic> word, bool isPractice})> _queue = [];
  bool _loading = true;
  bool _revealed = false;
  int _reviewed = 0;
  int _practiced = 0;
  int _lapses = 0;

  @override
  void initState() {
    super.initState();
    _loadSession();
  }

  Future<void> _loadSession() async {
    setState(() => _loading = true);

    _sessionSize = await LocalDatabase.getSessionSize();

    // Real reviews first: everything due, most overdue at the top.
    final due = await LocalDatabase.getDueWords(
      widget.language,
      limit: _sessionSize,
    );

    // If there's room left, fill the rest with practice items: the hardest
    // not-yet-due words. Practice never reschedules them.
    final practice = <Map<String, dynamic>>[];
    if (due.length < _sessionSize) {
      practice.addAll(
        await LocalDatabase.getHardestWords(
          widget.language,
          limit: _sessionSize - due.length,
        ),
      );
    }

    if (!mounted) return;
    setState(() {
      _queue = [
        ...due.map((w) => (word: w, isPractice: false)),
        ...practice.map((w) => (word: w, isPractice: true)),
      ];
      _loading = false;
      _revealed = false;
    });
  }

  bool get _hasSession => _queue.isNotEmpty;

  ({Map<String, dynamic> word, bool isPractice}) get _current => _queue.first;

  Future<void> _rate(Rating rating) async {
    if (!_hasSession || !_revealed) return;

    final item = _current;
    final word = item.word['word'] as String? ?? '';
    if (item.isPractice) {
      // Extra training: only records the practice timestamp, schedule stays.
      await LocalDatabase.practiceWord(word, widget.language, rating);
    } else {
      await LocalDatabase.reviewWord(word, widget.language, rating);
    }

    setState(() {
      _reviewed++;
      if (item.isPractice) _practiced++;
      _revealed = false;
      _queue.removeAt(0);
      if (rating == Rating.again) {
        // Show the word again later in this session. For practice reviews
        // this is purely extra exposure; it does not count as a lapse.
        if (!item.isPractice) _lapses++;
        _queue.add(item);
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(title: const Text('Training')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : !_hasSession
              ? _buildEmpty(theme)
              : _buildSession(theme),
    );
  }

  Widget _buildEmpty(ThemeData theme) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.emoji_events_outlined,
                size: 64, color: theme.colorScheme.primary),
            const SizedBox(height: 16),
            Text(
              _reviewed > 0 ? 'Session complete!' : 'No words saved yet',
              style: theme.textTheme.headlineSmall,
            ),
            const SizedBox(height: 8),
            Text(
              _reviewed > 0
                  ? 'You trained $_reviewed '
                      'word${_reviewed == 1 ? '' : 's'} '
                      '($_practiced practice, $_lapses needed repetition).'
                  : 'Save words first — then come back to train them.',
              textAlign: TextAlign.center,
              style: theme.textTheme.bodyLarge?.copyWith(
                color: theme.colorScheme.onSurfaceVariant,
              ),
            ),
            const SizedBox(height: 24),
            FilledButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Done'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSession(ThemeData theme) {
    final item = _current;
    final word = item.word;
    final isPractice = item.isPractice;
    final wordText = word['word'] as String? ?? 'Unknown word';
    final pronunciation = word['pronunciation'] as String?;
    final partOfSpeech = word['part_of_speech'] as String?;
    final gender = word['gender'] as String?;
    final senses = word['senses'] as List<dynamic>? ?? const [];
    final translations = senses
        .expand((s) => (s['translations'] as List<dynamic>? ?? const []))
        .map((t) => t.toString())
        .toList();

    return Column(
      children: [
        // Progress header
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 12, 16, 0),
          child: Row(
            children: [
              Text(
                '$_reviewed done · ${_queue.length} left',
                style: theme.textTheme.bodySmall?.copyWith(
                  color: theme.colorScheme.onSurfaceVariant,
                ),
              ),
            ],
          ),
        ),
        LinearProgressIndicator(
          value: _reviewed == 0 ? 0 : _reviewed / (_reviewed + _queue.length),
          minHeight: 4,
        ),
        Expanded(
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: Card(
              clipBehavior: Clip.antiAlias,
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Text(
                      wordText,
                      textAlign: TextAlign.center,
                      style: theme.textTheme.headlineMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    if (pronunciation != null) ...[
                      const SizedBox(height: 4),
                      Text('/$pronunciation/', textAlign: TextAlign.center),
                    ],
                    if (partOfSpeech != null) ...[
                      const SizedBox(height: 8),
                      Text(
                        partOfSpeech,
                        textAlign: TextAlign.center,
                        style: theme.textTheme.labelLarge,
                      ),
                    ],
                    if (isPractice) ...[
                      const SizedBox(height: 12),
                      Chip(
                        avatar: Icon(
                          Icons.fitness_center,
                          size: 16,
                          color: theme.colorScheme.primary,
                        ),
                        label: Text(
                          'Practice — schedule unchanged',
                          style: theme.textTheme.labelSmall,
                        ),
                        visualDensity: VisualDensity.compact,
                      ),
                    ],
                    if (_revealed) ...[
                      const SizedBox(height: 24),
                      if (gender != null)
                        Text(
                          'Gender: $gender',
                          style: const TextStyle(fontWeight: FontWeight.w600),
                        ),
                      if (gender != null) const SizedBox(height: 8),
                      Text(
                        translations.isEmpty
                            ? 'No translation available.'
                            : translations.join(', '),
                        textAlign: TextAlign.center,
                        style: theme.textTheme.titleMedium,
                      ),
                    ],
                    const SizedBox(height: 32),
                    FilledButton.tonal(
                      onPressed: _revealed
                          ? null
                          : () => setState(() => _revealed = true),
                      child: Text(_revealed ? 'Meaning revealed' : 'Reveal'),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
        // Grading bar
        SafeArea(
          child: Padding(
            padding: const EdgeInsets.fromLTRB(16, 4, 16, 16),
            child: Row(
              children: [
                for (final rating in Rating.values) ...[
                  Expanded(
                    child: _GradeButton(
                      rating: rating,
                      enabled: _revealed,
                      onPressed: () => _rate(rating),
                    ),
                  ),
                  if (rating != Rating.values.last) const SizedBox(width: 8),
                ],
              ],
            ),
          ),
        ),
      ],
    );
  }
}

class _GradeButton extends StatelessWidget {
  final Rating rating;
  final bool enabled;
  final VoidCallback onPressed;

  const _GradeButton({
    required this.rating,
    required this.enabled,
    required this.onPressed,
  });

  (String, Color) get _labelAndColor {
    switch (rating) {
      case Rating.again:
        return ('Again', Colors.red.shade400);
      case Rating.hard:
        return ('Hard', Colors.orange.shade400);
      case Rating.good:
        return ('Good', Colors.green.shade400);
      case Rating.easy:
        return ('Easy', Colors.teal.shade400);
    }
  }

  @override
  Widget build(BuildContext context) {
    final (label, color) = _labelAndColor;
    return FilledButton.tonal(
      onPressed: enabled ? onPressed : null,
      style: FilledButton.styleFrom(
        padding: const EdgeInsets.symmetric(vertical: 12),
        foregroundColor: enabled ? color : null,
      ),
      child: Text(label),
    );
  }
}
