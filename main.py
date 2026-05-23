"""
main.py
-------
MemoryMate: A Personal Forgetting Curve Study Scheduler
========================================================

Entry point for the MemoryMate application. Run this file to start:

    python main.py

MemoryMate tracks your study topics and applies the Ebbinghaus forgetting
curve to calculate exactly how much you remember right now — and exactly
when you need to review each topic before you forget it.

PROGRAM FLOW:
    1. Load topics from disk  (storage.py)
    2. Display the main menu
    3. User picks an action; action function is called
    4. Data is saved back to disk after every change
    5. Repeat until the user quits

ADVANCED CONCEPTS USED (COMP9001):
    - File I/O         : storage.py — JSON read/write for persistence
    - Custom Iterator  : scheduler.ReviewQueue — __iter__ / __next__
    - Recursion        : scheduler.compute_stability_recursive
    - Generators       : reports._topic_lines — yield for lazy I/O
    - More Flow Control: try/except throughout for robust user input

No external libraries required. Runs on Python 3.8+.

Author : [Your Name]
SID    : [Your SID]
Course : COMP9001 — Programming for Everyone, University of Sydney
"""

from scheduler import (
    compute_retention,
    compute_stability_recursive,
    next_review_in_days,
    ReviewQueue,
)
from storage import load_topics, save_topics
from reports import generate_report
from topic import Topic


# ─────────────────────────────────────────────────────────────────
#  Display utilities
# ─────────────────────────────────────────────────────────────────

_WIDTH = 52


def _header(title: str) -> None:
    """
    Print a formatted section header to the terminal.

    Args:
        title (str): Text to display inside the header box.
    """
    print("\n" + "=" * _WIDTH)
    print(f"  {title}")
    print("=" * _WIDTH)


def _sep() -> None:
    """Print a thin separator line."""
    print("-" * _WIDTH)


def _bar(retention: float, width: int = 22) -> str:
    """
    Build an ASCII progress bar representing a retention percentage.

    Args:
        retention (float) : Value between 0.0 and 1.0.
        width (int)       : Character width of the bar interior.

    Returns:
        str: Formatted string, e.g. '[████████░░░░░░]  63.2%'.
    """
    filled = round(retention * width)
    bar = "█" * filled + "░" * (width - filled)
    return f"[{bar}]  {retention * 100:.1f}%"


def _stars(confidence: int) -> str:
    """
    Return a star-rating string for a given confidence value.

    Args:
        confidence (int): Integer from 1 to 5.

    Returns:
        str: e.g. '★★★☆☆  (3/5)'
    """
    return "★" * confidence + "☆" * (5 - confidence) + f"  ({confidence}/5)"


# ─────────────────────────────────────────────────────────────────
#  Feature 1 — View today's review queue
# ─────────────────────────────────────────────────────────────────

def view_review_queue(topics: list) -> None:
    """
    Show all topics currently due for review, sorted by urgency.

    Uses the ReviewQueue custom iterator (scheduler.py) to walk through
    all topics and yield only those with retention below 70%.
    Topics with the lowest retention are displayed first.

    Args:
        topics (list): The full list of tracked Topic objects.
    """
    _header("Today's Review Queue")

    # Instantiate our custom iterator — this filters and sorts internally
    queue = ReviewQueue(topics)

    if queue.is_empty():
        print("\n  Nothing due for review. Great work!")
        print("  Come back tomorrow or add new topics.\n")
        return

    print(f"\n  {len(queue)} topic(s) need attention:\n")

    # Iterate using the custom __iter__ / __next__ protocol
    for retention, topic in queue:
        days = topic.days_since_last_review()
        next_days = next_review_in_days(topic.current_stability())
        print(f"  {topic.name}  ({topic.subject})")
        print(f"  Retention    : {_bar(retention)}")
        print(f"  Last reviewed: {days} day(s) ago")
        print(f"  Review now to reset — next due in {next_days} days after review.")
        _sep()


# ─────────────────────────────────────────────────────────────────
#  Feature 2 — Log a study session
# ─────────────────────────────────────────────────────────────────

def log_session(topics: list) -> None:
    """
    Record a new study session for a selected topic.

    Prompts the user to choose a topic and rate their confidence (1–5).
    Calls compute_stability_recursive to derive the new stability from the
    full confidence history, then saves the updated topic to disk.

    Args:
        topics (list): The full list of tracked Topic objects (modified in place).
    """
    _header("Log a Study Session")

    if not topics:
        print("\n  No topics yet. Add a topic first (option 5).")
        return

    print()
    for i, topic in enumerate(topics, 1):
        days = topic.days_since_last_review()
        stability = topic.current_stability()
        retention = compute_retention(stability, days)
        print(f"  {i:2d}.  {topic.name}  ({topic.subject})"
              f"  —  {retention * 100:.0f}% retained")

    _sep()

    try:
        choice = int(input("  Select topic number: ").strip())
        if not 1 <= choice <= len(topics):
            print("  Selection out of range.")
            return
    except ValueError:
        print("  Please enter a valid number.")
        return

    topic = topics[choice - 1]

    print(f"\n  Topic: {topic.name}")
    print("\n  Rate your confidence after studying this topic:")
    print("    1  Completely forgot — could not recall anything")
    print("    2  Vague memory — needed a lot of hints")
    print("    3  Partial recall — got the gist but gaps remain")
    print("    4  Good recall — minor hesitations only")
    print("    5  Perfect recall — instant and complete")

    try:
        confidence = int(input("\n  Confidence (1–5): ").strip())
        if not 1 <= confidence <= 5:
            print("  Please enter a value between 1 and 5.")
            return
    except ValueError:
        print("  Please enter a valid number.")
        return

    # ── Compute new stability recursively ───────────────────────
    # compute_stability_recursive derives stability from the confidence
    # history alone, without relying on stored stability values.
    # This is the ground-truth calculation.
    prior_stability = compute_stability_recursive(
        topic.review_history, len(topic.review_history) - 1
    )
    new_stability = prior_stability * (1 + 0.3 * confidence)

    topic.add_review(confidence, new_stability)
    save_topics(topics)

    next_days = next_review_in_days(new_stability)

    print(f"\n  Session logged.  Confidence: {_stars(confidence)}")
    print(f"  New stability : {new_stability:.3f}")
    print(f"  Next review   : in {next_days} day(s)\n")


# ─────────────────────────────────────────────────────────────────
#  Feature 3 — View all topics
# ─────────────────────────────────────────────────────────────────

def view_all_topics(topics: list) -> None:
    """
    Display every tracked topic with retention score and next review date.

    Topics are grouped alphabetically by subject for easy scanning.
    A status tag ('REVIEW NOW', 'Fading', 'Strong') gives a quick
    visual signal about each topic's urgency.

    Args:
        topics (list): The full list of tracked Topic objects.
    """
    _header("All Topics")

    if not topics:
        print("\n  No topics tracked yet. Add one with option 5.\n")
        return

    # Group by subject
    subjects = {}
    for topic in topics:
        subjects.setdefault(topic.subject, []).append(topic)

    for subject in sorted(subjects):
        print(f"\n  [ {subject.upper()} ]")
        _sep()
        for topic in subjects[subject]:
            days = topic.days_since_last_review()
            stability = topic.current_stability()
            retention = compute_retention(stability, days)
            next_days = next_review_in_days(stability)
            sessions = len(topic.review_history)

            if retention < 0.70:
                status = "REVIEW NOW"
            elif retention < 0.85:
                status = "Fading"
            else:
                status = "Strong"

            print(f"  {topic.name}")
            print(f"  {_bar(retention)}  [{status}]")
            print(f"  Sessions: {sessions}  |  Next review in: {next_days} day(s)")
            print()


# ─────────────────────────────────────────────────────────────────
#  Feature 4 — View topic review history
# ─────────────────────────────────────────────────────────────────

def view_topic_history(topics: list) -> None:
    """
    Display the complete review history for a selected topic.

    For each session, re-derives the stability using compute_stability_recursive
    to show how stability compounds across sessions. This lets the user verify
    that the recursive calculation matches the stored values.

    Args:
        topics (list): The full list of tracked Topic objects.
    """
    _header("Topic Review History")

    if not topics:
        print("\n  No topics tracked yet.\n")
        return

    print()
    for i, topic in enumerate(topics, 1):
        print(f"  {i:2d}. {topic.name}  ({topic.subject})")

    _sep()

    try:
        choice = int(input("  Select topic number: ").strip())
        if not 1 <= choice <= len(topics):
            print("  Selection out of range.")
            return
    except ValueError:
        print("  Please enter a valid number.")
        return

    topic = topics[choice - 1]

    print(f"\n  Topic  : {topic.name}")
    print(f"  Subject: {topic.subject}")
    print(f"  Added  : {topic.date_added}")
    _sep()

    if not topic.review_history:
        print("  No reviews logged for this topic yet.\n")
        return

    print(f"  {'#':>3}  {'Date':>12}  {'Confidence':>12}  {'Stability':>10}")
    _sep()

    for idx, session in enumerate(topic.review_history):
        # Recompute stability recursively for each session to verify
        derived_stability = compute_stability_recursive(topic.review_history, idx)
        print(
            f"  {idx + 1:>3}  {session.date:>12}  "
            f"{_stars(session.confidence):>12}  "
            f"{derived_stability:>10.4f}"
        )

    print()
    print(f"  Current stability : {topic.current_stability():.4f}")
    print(
        f"  Current retention : "
        f"{compute_retention(topic.current_stability(), topic.days_since_last_review()) * 100:.1f}%"
    )
    print()


# ─────────────────────────────────────────────────────────────────
#  Feature 5 — Add a new topic
# ─────────────────────────────────────────────────────────────────

def add_topic(topics: list) -> None:
    """
    Prompt the user to enter a new topic and add it to the system.

    Validates that the name is non-empty and not a case-insensitive
    duplicate of an existing topic. Saves the updated list to disk.

    Args:
        topics (list): The full list of tracked Topic objects (modified in place).
    """
    _header("Add a New Topic")

    name = input("\n  Topic name  (e.g. 'Binary Trees'): ").strip()
    if not name:
        print("  Topic name cannot be empty.")
        return

    # Reject duplicates (case-insensitive comparison)
    existing = [t.name.lower() for t in topics]
    if name.lower() in existing:
        print(f"  '{name}' is already tracked.")
        print("  Use 'Log a session' (option 2) to review it.")
        return

    subject = input("  Subject/category (e.g. 'COMP9001'): ").strip()
    if not subject:
        subject = "General"

    new_topic = Topic(name, subject)
    topics.append(new_topic)
    save_topics(topics)

    print(f"\n  Added '{name}' under '{subject}'.")
    print(f"  Initial stability: {Topic.INITIAL_STABILITY:.1f}")
    print(f"  First review recommended within 1 day.\n")


# ─────────────────────────────────────────────────────────────────
#  Feature 6 — Export weekly report
# ─────────────────────────────────────────────────────────────────

def export_report(topics: list) -> None:
    """
    Generate a weekly study report and export it to a dated text file.

    Calls generate_report() from reports.py, which uses a generator
    to write topic lines to the file one at a time.

    Args:
        topics (list): The full list of tracked Topic objects.
    """
    _header("Export Weekly Report")
    print("\n  Generating report...")
    try:
        filepath = generate_report(topics)
        print(f"  Report saved to: {filepath}\n")
    except OSError as err:
        print(f"  Could not write report: {err}\n")


# ─────────────────────────────────────────────────────────────────
#  Main menu
# ─────────────────────────────────────────────────────────────────

def _show_menu() -> None:
    """Print the main navigation menu to the terminal."""
    print("\n" + "=" * _WIDTH)
    print("  MEMORYMATE  —  Forgetting Curve Scheduler")
    print("=" * _WIDTH)
    print("  1.  View review queue  (what to study today)")
    print("  2.  Log a study session")
    print("  3.  View all topics + retention scores")
    print("  4.  View topic review history")
    print("  5.  Add a new topic")
    print("  6.  Export weekly report")
    print("  7.  Quit")
    print("=" * _WIDTH)


def main() -> None:
    """
    Main entry point for MemoryMate.

    Loads persisted topic data from disk, displays the menu, and
    dispatches user choices to the appropriate action function.
    All changes are saved to disk automatically after each action.
    The loop continues until the user selects option 7 (Quit).
    """
    print("\n" + "=" * _WIDTH)
    print("  Welcome to MemoryMate")
    print("  Study smarter with the Ebbinghaus forgetting curve.")
    print("=" * _WIDTH)

    # Load persisted data — returns [] on first run
    topics = load_topics()

    if topics:
        # Quick summary on startup
        due = sum(
            1 for t in topics
            if compute_retention(
                t.current_stability(), t.days_since_last_review()
            ) < 0.70
        )
        print(f"\n  {len(topics)} topic(s) tracked  |  {due} due for review today.")
    else:
        print("\n  No topics yet. Add your first topic with option 5.")

    # Map menu numbers to (function, takes_topics)
    actions = {
        "1": view_review_queue,
        "2": log_session,
        "3": view_all_topics,
        "4": view_topic_history,
        "5": add_topic,
        "6": export_report,
    }

    while True:
        _show_menu()
        choice = input("  Enter choice (1–7): ").strip()

        if choice == "7":
            print("\n  Goodbye. Keep reviewing!\n")
            break
        elif choice in actions:
            actions[choice](topics)
        else:
            print("  Invalid choice. Please enter a number from 1 to 7.")


if __name__ == "__main__":
    main()
