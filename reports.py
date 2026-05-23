"""
reports.py
----------
Generates a weekly study report and exports it as a plain-text file.

The report groups all tracked topics by subject, shows current retention
percentages, stability values, and review session counts — giving the user
a clear snapshot of their study health across all topics.

The report filename includes today's date so multiple reports accumulate
in the reports/ directory without overwriting each other.

Output location: reports/report_YYYY-MM-DD.txt

Advanced concept demonstrated:
    Generator function (_topic_lines) yields formatted lines one at a time
    using the 'yield' keyword, avoiding building the full report in memory.
"""

import os
from datetime import date
from scheduler import compute_retention, next_review_in_days, REVIEW_THRESHOLD

_REPORT_DIR = "reports"
_LINE_WIDTH = 48


def _divider(char: str = "-") -> str:
    """
    Return a horizontal divider string of standard line width.

    Args:
        char (str): Character to repeat. Defaults to '-'.

    Returns:
        str: Divider line of _LINE_WIDTH characters.
    """
    return char * _LINE_WIDTH


def _retention_label(retention: float) -> str:
    """
    Return a short status label based on the retention value.

    Args:
        retention (float): Current retention between 0.0 and 1.0.

    Returns:
        str: Human-readable status string.
    """
    if retention >= 0.85:
        return "Strong"
    if retention >= REVIEW_THRESHOLD:
        return "Fading"
    return "REVIEW NOW"


def _topic_lines(topics: list):
    """
    Generator that yields formatted report lines for a list of topics.

    Uses Python's 'yield' keyword to produce one line at a time.
    This means the file is written incrementally rather than building
    a giant string in memory before writing — efficient for large datasets.

    Args:
        topics (list): List of Topic objects to format.

    Yields:
        str: A single line of formatted text for the report file.
    """
    for topic in topics:
        days = topic.days_since_last_review()
        stability = topic.current_stability()
        retention = compute_retention(stability, days)
        sessions = len(topic.review_history)
        next_days = next_review_in_days(stability)
        status = _retention_label(retention)

        yield f"  Topic      : {topic.name}"
        yield f"  Added      : {topic.date_added}"
        yield f"  Retention  : {retention * 100:.1f}%  [{status}]"
        yield f"  Stability  : {stability:.3f}"
        yield f"  Sessions   : {sessions}"
        yield f"  Next review: in {next_days} day(s)"
        yield _divider()


def generate_report(topics: list) -> str:
    """
    Generate a weekly report and write it to a timestamped text file.

    Topics are grouped by subject for readability. The generator
    _topic_lines() is used to write each topic's section line by line.

    Args:
        topics (list): All Topic objects currently tracked in the system.

    Returns:
        str: The relative filepath where the report was written.

    Raises:
        OSError: If the reports directory cannot be created or the file
                 cannot be written.
    """
    if not os.path.exists(_REPORT_DIR):
        os.makedirs(_REPORT_DIR)

    today = date.today()
    filename = f"report_{today}.txt"
    filepath = os.path.join(_REPORT_DIR, filename)

    with open(filepath, "w", encoding="utf-8") as f:

        # ── Header ──────────────────────────────────────────
        f.write(_divider("=") + "\n")
        f.write("  MEMORYMATE — WEEKLY STUDY REPORT\n")
        f.write(f"  Generated : {today}\n")
        f.write(_divider("=") + "\n\n")

        if not topics:
            f.write("  No topics tracked yet.\n")
            f.write("  Run MemoryMate and add topics to get started.\n")

        else:
            f.write(f"  Topics tracked : {len(topics)}\n")

            # Count how many are currently due
            due_count = sum(
                1 for t in topics
                if compute_retention(t.current_stability(), t.days_since_last_review())
                < REVIEW_THRESHOLD
            )
            f.write(f"  Due for review : {due_count}\n\n")

            # ── Group topics by subject ──────────────────────
            subjects = {}
            for topic in topics:
                subjects.setdefault(topic.subject, []).append(topic)

            for subject, subject_topics in sorted(subjects.items()):
                f.write(f"\n  [ {subject.upper()} ]\n")
                f.write(_divider() + "\n")

                # Write lines from the generator one at a time
                for line in _topic_lines(subject_topics):
                    f.write(line + "\n")

        # ── Footer ──────────────────────────────────────────
        f.write("\n" + _divider("=") + "\n")
        f.write("  Memory is a muscle. Keep reviewing.\n")
        f.write(_divider("=") + "\n")

    return filepath
