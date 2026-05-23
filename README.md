# MemoryMate — Forgetting Curve Study Scheduler

> *Study smarter, not harder. Review what you're about to forget — not what you already know.*

![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)
![Course](https://img.shields.io/badge/COMP9001-University%20of%20Sydney-orange)
![Status](https://img.shields.io/badge/Status-Complete-brightgreen)

---

## What is MemoryMate?

Most students re-read notes they already know perfectly — and completely forget topics they studied two weeks ago. Both problems have the same root cause: studying without a schedule.

**MemoryMate** applies the **Ebbinghaus forgetting curve** (1885) to calculate exactly how much you remember right now, and exactly when you need to review each topic before retention drops too low. Every time you review with high confidence, your memory stability compounds and the next review is pushed further into the future.

No internet. No accounts. No subscriptions. Just Python and a JSON file.

---

## The Science

The forgetting curve formula driving MemoryMate:

```
R(t) = e ^ (-t / S)
```

| Symbol | Meaning |
|--------|---------|
| `R` | Retention — how much you currently remember (0.0 – 1.0) |
| `t` | Days elapsed since the last review |
| `S` | Memory stability — increases with each confident review |

After each review session, stability updates based on your self-rated confidence (1–5):

```
S_new = S_old × (1 + 0.3 × confidence)
```

A topic enters the review queue when **R drops below 70%**. The more confident you are each session, the longer the gap before the next review — just like Anki, but fully transparent.

---

## Features

| # | Feature | Description |
|---|---------|-------------|
| 1 | **Review Queue** | Today's due topics, sorted by urgency (lowest retention first) |
| 2 | **Log a Session** | Record a study session and rate your confidence 1–5 |
| 3 | **All Topics** | Full list with live retention scores and next review dates |
| 4 | **Topic History** | Per-session breakdown with recursively derived stability values |
| 5 | **Add a Topic** | Add a new topic to any subject category |
| 6 | **Export Report** | Save a weekly study health report as a `.txt` file |

---

## Getting Started

**Requirements:** Python 3.8 or higher. No external libraries needed.

```bash
# Clone the repository
git clone https://github.com/dvijkantsharma/memorymate.git
cd memorymate

# Run the program
python main.py
```

That's it. The `data/` directory and `topics.json` file are created automatically on first run.

---

## Project Structure

```
memorymate/
├── main.py         # Entry point — menu loop and all user interactions
├── topic.py        # Topic and ReviewSession classes
├── scheduler.py    # Forgetting curve math, recursive stability, ReviewQueue iterator
├── storage.py      # File I/O — load and save topics as JSON
├── reports.py      # Weekly report generator (uses Python generators)
└── data/
    └── topics.json # Persistent storage (auto-created, gitignored)
```

---

## Demo

```
====================================================
  MEMORYMATE  —  Forgetting Curve Scheduler
====================================================
  1.  View review queue  (what to study today)
  2.  Log a study session
  3.  View all topics + retention scores
  4.  View topic history
  5.  Add a new topic
  6.  Export weekly report
  7.  Quit
====================================================

====================================================
  Today's Review Queue
====================================================

  Binary Trees  (COMP9001)
  Retention    : [████████░░░░░░░░░░░░░░]  43.2%
  Last reviewed: 8 day(s) ago
  Review now to reset — next due in 2 days after review.
--------------------------------------------------
  Recursion  (COMP9001)
  Retention    : [█████████████░░░░░░░░░]  61.5%
  Last reviewed: 5 day(s) ago
  Review now to reset — next due in 5 days after review.
--------------------------------------------------
```

---

## Advanced Concepts (COMP9001)

| Concept | File | Implementation |
|---------|------|----------------|
| **File I/O** | `storage.py` | Topics persisted as JSON; loaded at startup, saved after every action |
| **Custom Iterator** | `scheduler.py` | `ReviewQueue` implements `__iter__` and `__next__` to lazily yield due topics |
| **Recursion** | `scheduler.py` | `compute_stability_recursive` re-derives stability from confidence history |
| **Generators** | `reports.py` | `_topic_lines` uses `yield` to write report lines one at a time |
| **Classes & Objects** | `topic.py` | `Topic` and `ReviewSession` with serialisation and class methods |

---

## Author

**Dvij Kant Sharma**  
MSc Computer Science (Cybersecurity & AI) — University of Sydney  
[github.com/dvijkantsharma](https://github.com/dvijkantsharma)

---

*Built for COMP9001 — Programming for Everyone, Semester 1 2026.*
