import 'package:flutter/material.dart';
import 'package:conlang/widgets/dashboard_tile.dart';

/// Tile showing activity summary: training streak, words studied per day.
class ActivityTile extends StatelessWidget {
  /// Placeholder data – replace with real API/local DB queries later.
  final int streakDays;
  final List<int> recentWords; // words studied per day, last 7 days

  const ActivityTile({
    super.key,
    this.streakDays = 0,
    this.recentWords = const [0, 0, 0, 0, 0, 0, 0],
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final totalWords = recentWords.fold(0, (a, b) => a + b);

    return DashboardTile(
      title: 'Activity',
      icon: Icons.trending_up,
      color: theme.colorScheme.secondary,
      body: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Streak row
          Row(
            children: [
              const Icon(Icons.local_fire_department,
                  color: Colors.deepOrange, size: 28),
              const SizedBox(width: 8),
              Text(
                '$streakDays-day streak',
                style: theme.textTheme.titleMedium?.copyWith(
                  fontWeight: FontWeight.bold,
                ),
              ),
              const Spacer(),
              Text('$totalWords words',
                  style: theme.textTheme.bodySmall),
            ],
          ),
          const SizedBox(height: 12),
          // Mini bar chart for the last 7 days
          Expanded(
            child: _MiniBarChart(
              values: recentWords,
              barColor: theme.colorScheme.secondary,
              maxBarValue: recentWords
                  .reduce((a, b) => a > b ? a : b),
            ),
          ),
          const SizedBox(height: 4),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: List.generate(7, (i) {
              return Text(
                _dayLabel(i),
                style: theme.textTheme.labelSmall?.copyWith(
                  color: theme.colorScheme.onSurfaceVariant,
                ),
              );
            }),
          ),
        ],
      ),
    );
  }

  String _dayLabel(int daysAgo) {
    final now = DateTime.now();
    final d = now.subtract(Duration(days: 6 - daysAgo));
    return ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][d.weekday - 1];
  }
}

class _MiniBarChart extends StatelessWidget {
  final List<int> values;
  final Color barColor;
  final int maxBarValue;

  const _MiniBarChart({
    required this.values,
    required this.barColor,
    required this.maxBarValue,
  });

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        // Use up to 60% of available height for bars, rest for labels
        final maxBarHeight = constraints.maxHeight * 0.6;
        final labelStyle = Theme.of(context).textTheme.labelSmall?.copyWith(
              fontWeight: FontWeight.w600,
            );

        return Row(
          crossAxisAlignment: CrossAxisAlignment.end,
          children: values.map((v) {
            final fraction = maxBarValue > 0 ? v / maxBarValue : 0.0;
            return Expanded(
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 2),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    if (v > 0)
                      Text('$v', style: labelStyle),
                    const SizedBox(height: 2),
                    Container(
                      height: fraction * maxBarHeight,
                      decoration: BoxDecoration(
                        color: barColor.withValues(alpha: 0.3 + fraction * 0.5),
                        borderRadius: const BorderRadius.vertical(
                          top: Radius.circular(4),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            );
          }).toList(),
        );
      },
    );
  }
}