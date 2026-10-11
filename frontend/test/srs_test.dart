import 'package:flutter_test/flutter_test.dart';
import 'package:conlang/services/srs.dart';

void main() {
  final now = DateTime(2026, 1, 1);

  group('scheduleReview', () {
    test('new word rated good: 1 day interval', () {
      final r = scheduleReview(const ReviewState(), Rating.good, now);
      expect(r.state.repetitions, 1);
      expect(r.state.intervalDays, 1);
      expect(r.dueAt, now.add(const Duration(days: 1)));
    });

    test('second success: 6 day interval', () {
      final r = scheduleReview(
        const ReviewState(repetitions: 1, intervalDays: 1),
        Rating.good,
        now,
      );
      expect(r.state.repetitions, 2);
      expect(r.state.intervalDays, 6);
      expect(r.dueAt, now.add(const Duration(days: 6)));
    });

    test('third success grows interval by ease factor', () {
      final r = scheduleReview(
        const ReviewState(easeFactor: 2.5, repetitions: 2, intervalDays: 6),
        Rating.good,
        now,
      );
      expect(r.state.repetitions, 3);
      // 6 * (2.5 + 0) = 15
      expect(r.state.intervalDays, 15);
      expect(r.dueAt, now.add(const Duration(days: 15)));
    });

    test('easy increases ease factor, hard decreases it', () {
      final easy = scheduleReview(
        const ReviewState(repetitions: 2, intervalDays: 6),
        Rating.easy,
        now,
      );
      expect(easy.state.easeFactor, greaterThan(2.5));

      final hard = scheduleReview(
        const ReviewState(repetitions: 2, intervalDays: 6),
        Rating.hard,
        now,
      );
      expect(hard.state.easeFactor, lessThan(2.5));
      // 6 * (2.5 - 0.14) = 14.16 -> 14
      expect(hard.state.intervalDays, 14);
    });

    test('again resets progress and schedules a relearn delay', () {
      final r = scheduleReview(
        const ReviewState(easeFactor: 2.5, repetitions: 4, intervalDays: 20),
        Rating.again,
        now,
      );
      expect(r.state.repetitions, 0);
      expect(r.state.intervalDays, 0);
      expect(r.state.easeFactor, lessThan(2.5));
      expect(r.dueAt, now.add(const Duration(minutes: 10)));
    });

    test('ease factor never drops below 1.3', () {
      var state = const ReviewState();
      // Repeated lapses keep pushing EF down, but must clamp at 1.3.
      for (var i = 0; i < 20; i++) {
        state = scheduleReview(state, Rating.again, now).state;
      }
      expect(state.easeFactor, 1.3);
    });

    test('successful review after a lapse starts at 1 day again', () {
      final lapsed = scheduleReview(
        const ReviewState(repetitions: 3, intervalDays: 15),
        Rating.again,
        now,
      ).state;

      final recovered = scheduleReview(lapsed, Rating.good, now);
      expect(recovered.state.repetitions, 1);
      expect(recovered.state.intervalDays, 1);
    });
  });
}
