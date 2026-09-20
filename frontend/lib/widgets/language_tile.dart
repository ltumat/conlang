import 'package:flutter/material.dart';
import 'package:conlang/screens/language_screen.dart';
import 'package:conlang/services/local_database.dart';

/// The first tile on the dashboard. Occupies 200 px total, split into
/// a language picker bar and a "Go to training" button with space between.
class LanguageTile extends StatefulWidget {
  final String name;
  final int wordCount;

  const LanguageTile({super.key, required this.name, required this.wordCount});

  @override
  State<LanguageTile> createState() => _LanguageTileState();
}

class _LanguageTileState extends State<LanguageTile> {
  final _languages = ['French', 'Spanish', 'Chinese', 'Arabic', 'German'];
  late String _current;
  int _savedCount = 0;

  @override
  void initState() {
    super.initState();
    _current = widget.name;
    _loadSavedCount();
  }

  Future<void> _loadSavedCount() async {
    final count = await LocalDatabase.getSavedWordCount(_current);
    if (mounted) setState(() => _savedCount = count);
  }

  void _openLanguageScreen() async {
    await Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => LanguageScreen(language: _current),
      ),
    );
    // Refresh saved count when coming back
    _loadSavedCount();
  }

  void _pickLanguage(BuildContext context) {
    showModalBottomSheet(
      context: context,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (sheetContext) {
        return SafeArea(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const SizedBox(height: 12),
              Container(
                width: 40,
                height: 4,
                decoration: BoxDecoration(
                  color: Theme.of(context)
                      .colorScheme
                      .onSurfaceVariant
                      .withValues(alpha: 0.4),
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
              const SizedBox(height: 20),
              Text(
                'Choose a language',
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.w600,
                    ),
              ),
              const SizedBox(height: 8),
              Flexible(
                child: ListView.builder(
                  shrinkWrap: true,
                  itemCount: _languages.length,
                  itemBuilder: (_, i) {
                    final lang = _languages[i];
                    return ListTile(
                      leading: Icon(
                        lang == _current
                            ? Icons.check_circle
                            : Icons.language,
                        color: lang == _current
                            ? Theme.of(context).colorScheme.primary
                            : null,
                      ),
                      title: Text(lang),
                      trailing: lang == _current
                          ? null
                          : const Icon(Icons.chevron_right),
                      onTap: () {
                        setState(() {
                          _current = lang;
                          _loadSavedCount();
                        });
                        Navigator.pop(sheetContext);
                      },
                    );
                  },
                ),
              ),
              const SizedBox(height: 8),
            ],
          ),
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    final tileShape = RoundedRectangleBorder(
      borderRadius: BorderRadius.circular(12),
    );

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        // ── Language picker (card) ──────────────────────────────────
        Card(
          elevation: 1,
          shape: tileShape,
          clipBehavior: Clip.antiAlias,
          color: theme.colorScheme.surfaceContainerHighest,
          child: SizedBox(
            height: 48,
            child: InkWell(
              onTap: () => _pickLanguage(context),
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16),
                child: Row(
                  children: [
                    Icon(Icons.translate,
                        color: theme.colorScheme.onSurface, size: 20),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        _current,
                        style: theme.textTheme.titleSmall?.copyWith(
                          color: const Color(0xFF1B5E20),
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),
                    Icon(Icons.arrow_drop_down,
                        color: theme.colorScheme.onSurface.withValues(alpha: 0.6),
                        size: 22),
                  ],
                ),
              ),
            ),
          ),
        ),
        const SizedBox(height: 2),
        // ── Go-to-training (card, fills remaining space) ────────────
        Expanded(
          child: Card(
            elevation: 1,
            shape: tileShape,
            clipBehavior: Clip.antiAlias,
            child: InkWell(
              onTap: _openLanguageScreen,
              child: Center(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(Icons.menu_book_rounded,
                            size: 18,
                            color: theme.colorScheme.onSurface),
                        const SizedBox(width: 10),
                        Text(
                          'Go to training',
                          style: theme.textTheme.titleMedium?.copyWith(
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                        const SizedBox(width: 8),
                        Icon(Icons.arrow_forward_ios_rounded,
                            size: 14,
                            color: theme.colorScheme.onSurfaceVariant),
                      ],
                    ),
                    const SizedBox(height: 4),
                    Text(
                      '$_savedCount words saved',
                      style: theme.textTheme.bodySmall?.copyWith(
                        color: theme.colorScheme.onSurfaceVariant,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ],
    );
  }
}