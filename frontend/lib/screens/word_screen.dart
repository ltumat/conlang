import 'package:flutter/material.dart';

class WordScreen extends StatefulWidget {
  final Map<String, dynamic> word;

  const WordScreen({super.key, required this.word});

  @override
  State<WordScreen> createState() => _WordScreenState();
}

class _WordScreenState extends State<WordScreen> {
  bool _revealed = false;
  bool _showConjugations = false;

  List<dynamic> get _senses =>
      widget.word['senses'] as List<dynamic>? ?? const [];

  @override
  Widget build(BuildContext context) {
    final word = widget.word['word'] as String? ?? 'Unknown word';
    final pronunciation = widget.word['pronunciation'] as String?;
    final partOfSpeech = widget.word['part_of_speech'] as String?;
    final gender = widget.word['gender'] as String?;

    return Scaffold(
      appBar: AppBar(title: Text(word)),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Card(
          clipBehavior: Clip.antiAlias,
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Text(
                  word,
                  textAlign: TextAlign.center,
                  style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                ),
                if (pronunciation != null) ...[
                  const SizedBox(height: 4),
                  Text('/$pronunciation/', textAlign: TextAlign.center),
                ],
                const SizedBox(height: 12),
                Center(
                  child: Text(
                    partOfSpeech ?? 'Word kind unavailable',
                    style: Theme.of(context).textTheme.labelLarge,
                  ),
                ),
                AnimatedCrossFade(
                  duration: const Duration(milliseconds: 350),
                  crossFadeState: _revealed
                      ? CrossFadeState.showSecond
                      : CrossFadeState.showFirst,
                  firstChild: const SizedBox(height: 24),
                  secondChild: Padding(
                    padding: const EdgeInsets.only(top: 24),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        if (gender != null)
                          Text(
                            'Gender: $gender',
                            style: const TextStyle(
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        if (gender != null) const SizedBox(height: 8),
                        for (var i = 0; i < _senses.length; i++)
                          _MeaningSection(
                            number: _senses[i]['number'] ?? i + 1,
                            translations: (_senses[i]['translations']
                                        as List<dynamic>? ??
                                    const [])
                                .map((translation) => translation.toString())
                                .toList(),
                            isLast: i == _senses.length - 1,
                          ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 16),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    OutlinedButton.icon(
                      onPressed: () => setState(
                        () => _showConjugations = !_showConjugations,
                      ),
                      icon: const Icon(Icons.menu_book_outlined),
                      label: const Text('Conjugations'),
                    ),
                    FilledButton(
                      onPressed: () => setState(() => _revealed = !_revealed),
                      child: Text(_revealed ? 'Hide' : 'Reveal'),
                    ),
                  ],
                ),
                if (_showConjugations) ...[
                  const SizedBox(height: 20),
                  _ConjugationTable(
                    conjugations: widget.word['conjugations']
                        as Map<String, dynamic>?,
                  ),
                ],
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _MeaningSection extends StatelessWidget {
  final dynamic number;
  final List<String> translations;
  final bool isLast;

  const _MeaningSection({
    required this.number,
    required this.translations,
    required this.isLast,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      margin: EdgeInsets.only(bottom: isLast ? 0 : 12),
      padding: const EdgeInsets.only(top: 10, left: 12, right: 12, bottom: 10),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surfaceContainerHighest,
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Meaning $number',
            style: const TextStyle(fontWeight: FontWeight.w700),
          ),
          const SizedBox(height: 4),
          if (translations.isEmpty)
            const Text('No translation available.')
          else
            Text(
              translations.join(', '),
              style: Theme.of(context).textTheme.titleMedium,
            ),
        ],
      ),
    );
  }
}

class _ConjugationTable extends StatelessWidget {
  final Map<String, dynamic>? conjugations;

  const _ConjugationTable({required this.conjugations});

  @override
  Widget build(BuildContext context) {
    if (conjugations == null || conjugations!.isEmpty) {
      return const Text('No conjugations available yet.');
    }
    final present = conjugations!['present'] as Map<String, dynamic>?;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('Present tense', style: Theme.of(context).textTheme.titleMedium),
        if (present != null)
          ...present.entries.map(
            (entry) => Padding(
              padding: const EdgeInsets.only(top: 4),
              child: Text('${entry.key}: ${entry.value}'),
            ),
          ),
        if (conjugations!['past_participle'] != null)
          Padding(
            padding: const EdgeInsets.only(top: 4),
            child: Text(
              'Past participle: ${conjugations!['past_participle']}',
            ),
          ),
      ],
    );
  }
}
