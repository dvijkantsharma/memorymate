"""
scheduler.py
------------
Core logic for the Ebbinghaus forgetting curve and the ReviewQueue iterator.

FORGETTING CURVE FORMULA (Ebbinghaus, 1885):
    R(t) = e ^ (-t / S)

    R  : retention value, range 0.0 – 1.0
    t  : days elapsed since the last review
    S  : memory stability (higher = slower forgetting)

STABILITY UPDATE RULE (applied after each review session):
    S_new = S_old * (1 + 0.3 * confidence)

    confidence : user self-rating from 1 (complete blank) to 5 (perfect recall)
    A confidence of 5 roughly doubles stability each session, so the
    interval between reviews grows exponentially with repeated success.

REVIEW THRESHOLD:
    A topic enters the review queue when R < 0.70 (i.e. 70% retention).

Advanced concepts demonstrated in this file:
    - Custom iterator class (ReviewQueue) via __iter__ / __next__
    - Recursive function (compute_stability_recursive)
"""

import math
from topic import Topic

# Retention threshold below which a topic is marked as due for review
REVIEW_THRESHOLD = 0.70


# ─────────────────────────────────────────
#  Core curve calculations
# ─────────────────────────────────────────

def compute_retention(stability: float, days: float) -> float:
    """
    Compute current memory retention using the Ebbinghaus forgetting curve.

    Formula: R = e ^ (-t / S)

    A retention of 1.0 means perfect recall; 0.0 means complete forgetting.
    Returns 1.0 immediately after a review (days = 0).

    Args:
        stability (float) : Memory stability for this topic.
        days (float)      : Days elapsed since the last review.

    Returns:
        float: Retention value between 0.0 and 1.0.

    Examples:
        >>> compute_retention(5.0, 0)
        1.0
        >>> round(compute_retention(5.0, 5), 3)
        0.368
    """
    if days <= 0:
        return 1.0
    return math.exp(-days / stability)


def compute_stability_recursive(sessions: list, idx: int) -> float:
    """
    Recursively compute cumulative memory stability across review sessions.

    Works backwards from the earliest session, multiplying each session's
    stability contribution onto the result of all prior sessions.

    BASE CASE  : idx < 0 — no sessions yet, return INITIAL_STABILITY (1.0).
    RECURSIVE  : compute stability of all sessions before idx, then apply
                 the update rule using this session's confidence rating.

    This function re-derives stability purely from the confidence history,
    independent of the stored stability field, making it a verifiable
    ground-truth calculation.

    Args:
        sessions (list) : Chronological list of ReviewSession objects.
        idx (int)       : Index of the session to compute up to (inclusive).

    Returns:
        float: Cumulative stability after the session at position idx.

    Examples:
        >>> from topic import ReviewSession
        >>> s = [ReviewSession('2025-01-01', 3, 0), ReviewSession('2025-01-02', 5, 0)]
        >>> round(compute_stability_recursive(s, 0), 3)  # Only session 0
        1.9
        >>> round(compute_stability_recursive(s, 1), 3)  # Both sessions
        3.8
    """
    # Base case: before any sessions, return the initial stability constant
    if idx < 0:
        return Topic.INITIAL_STABILITY

    # Recursive step: compute stability from all prior sessions first
    prior_stability = compute_stability_recursive(sessions, idx - 1)

    # Apply stability update rule for this session's confidence rating
    confidence = sessions[idx].confidence
    return prior_stability * (1 + 0.3 * confidence)


def next_review_in_days(stability: float, threshold: float = REVIEW_THRESHOLD) -> int:
    """
    Calculate how many days until the next review should be scheduled.

    Solves for t in: threshold = e ^ (-t / S)
    Rearranges to:   t = -S * ln(threshold)

    Args:
        stability (float)  : Current memory stability for the topic.
        threshold (float)  : Retention level that triggers a review.
                             Defaults to REVIEW_THRESHOLD (0.70).

    Returns:
        int: Days from today until the next recommended review (minimum 1).
    """
    days = -stability * math.log(threshold)
    return max(1, round(days))


# ─────────────────────────────────────────
#  ReviewQueue iterator  (Advanced topic)
# ─────────────────────────────────────────

class ReviewQueue:
    """
    A custom iterator that yields topics due for review today.

    A topic is included when its current retention drops below REVIEW_THRESHOLD.
    Topics are sorted by urgency — the most forgotten (lowest retention) appear
    first so the user always tackles the most critical review first.

    Implements the full Python iterator protocol:
        __iter__  : returns self (this object is its own iterator)
        __next__  : returns the next (retention, topic) tuple or raises StopIteration

    Attributes:
        _due (list)  : Sorted list of (retention, topic) tuples for due topics.
        _index (int) : Current position in the iteration.

    Example usage:
        queue = ReviewQueue(all_topics)
        for retention, topic in queue:
            print(f"{topic.name}: {retention * 100:.1f}% retained")
    """

    def __init__(self, topics: list) -> None:
        """
        Build the review queue by filtering and ranking all topics.

        For each topic, compute its current retention. Topics with retention
        below REVIEW_THRESHOLD are collected, then sorted ascending by
        retention so the most urgent reviews come first.

        Args:
            topics (list): All Topic objects currently tracked in the system.
        """
        due = []
        for topic in topics:
            days = topic.days_since_last_review()
            stability = topic.current_stability()
            retention = compute_retention(stability, days)
            if retention < REVIEW_THRESHOLD:
                due.append((retention, topic))

        # Sort ascending: lowest retention (most forgotten) reviewed first
        self._due = sorted(due, key=lambda pair: pair[0])
        self._index = 0

    def __iter__(self) -> "ReviewQueue":
        """
        Return the iterator object itself.

        Required by the iterator protocol. Allows ReviewQueue to be used
        directly in a for-loop without a separate call to iter().

        Returns:
            ReviewQueue: This instance.
        """
        return self

    def __next__(self) -> tuple:
        """
        Return the next (retention, topic) tuple in the queue.

        Returns:
            tuple: (float retention, Topic object) for the next due topic.

        Raises:
            StopIteration: When all due topics have been yielded.
        """
        if self._index >= len(self._due):
            raise StopIteration
        item = self._due[self._index]
        self._index += 1
        return item

    def __len__(self) -> int:
        """
        Return the total number of topics currently due for review.

        Returns:
            int: Count of due topics in this queue.
        """
        return len(self._due)

    def is_empty(self) -> bool:
        """
        Check whether the review queue is empty.

        Returns:
            bool: True if no topics are due, False otherwise.
        """
        return len(self._due) == 0
