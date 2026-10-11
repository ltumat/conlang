library;

enum Rating {
  again,
  hard,
  good,
  easy,
}

/// The quality score used by the SM-2 formula (0–5).
int _qualityOf(Rating rating) {
  switch (rating) {
    case Rating.again:
      return 2;
    case Rating.hard:
      return 3;
    case Rating.good:
      return 4;
    case Rating.easy:
      return 5;
  }
}

/// The scheduling state of a single word.
class ReviewState {
  final double easeFactor;
  final int repetitions;
  final double intervalDays;

  const ReviewState({
    this.easeFactor = 2.5,
    this.repetitions = 0,
    this.intervalDays = 0,
  });

  /// Whether this word has never been reviewed.
  bool get isNew => repetitions == 0 && intervalDays == 0;

  ReviewState copyWith({
    double? easeFactor,
    int? repetitions,
    double? intervalDays,
  }) {
    return ReviewState(
      easeFactor: easeFactor ?? this.easeFactor,
      repetitions: repetitions ?? this.repetitions,
      intervalDays: intervalDays ?? this.intervalDays,
    );
  }
}

/// The result of applying a review to a [ReviewState].
class ScheduleResult {
  final ReviewState state;

  /// When the word should be reviewed next.
  final DateTime dueAt;

  const ScheduleResult({required this.state, required this.dueAt});
}

/// Short delay before a lapsed word is shown again (within the session).
const _relearnDelay = Duration(minutes: 10);

const _minEaseFactor = 1.3;

/// Apply one review with the given [rating], returning the updated state and
/// the next due date.
ScheduleResult scheduleReview(
  ReviewState state,
  Rating rating,
  DateTime now,
) {
  final q = _qualityOf(rating);

  // Ease factor update (SM-2 formula), clamped to a minimum of 1.3.
  final newEase = (state.easeFactor + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02)))
      .clamp(_minEaseFactor, double.infinity);

  ReviewState next;
  DateTime dueAt;

  if (q < 3) {
    // Lapse: reset progress; show the word again soon to relearn it.
    next = state.copyWith(easeFactor: newEase, repetitions: 0, intervalDays: 0);
    dueAt = now.add(_relearnDelay);
  } else {
    // Success: grow the interval 1 day -> 6 days -> interval * ease factor.
    double interval;
    if (state.repetitions == 0) {
      interval = 1;
    } else if (state.repetitions == 1) {
      interval = 6;
    } else {
      interval = (state.intervalDays * newEase).roundToDouble();
    }
    next = state.copyWith(
      easeFactor: newEase,
      repetitions: state.repetitions + 1,
      intervalDays: interval,
    );
    dueAt = now.add(Duration(days: interval.round()));
  }

  return ScheduleResult(state: next, dueAt: dueAt);
}
