"""
storage.py
----------
Handles all file input/output (I/O) operations for MemoryMate.

Topic data is persisted as a human-readable JSON file inside a 'data/'
directory. This module provides two public functions:

    load_topics()        -- Read topics from disk at startup.
    save_topics(topics)  -- Write topics back to disk after any change.

The data directory and JSON file are created automatically on first run,
so the user never needs to create them manually.

File location: data/topics.json

Advanced concept demonstrated: File I/O (Week 8)
"""

import json
import os
from topic import Topic

# Paths for the persistent data file
_DATA_DIR = "data"
_DATA_FILE = os.path.join(_DATA_DIR, "topics.json")


def _ensure_data_dir() -> None:
    """
    Create the data directory if it does not already exist.

    Called internally by both load_topics and save_topics before
    any file operation is attempted.
    """
    if not os.path.exists(_DATA_DIR):
        os.makedirs(_DATA_DIR)


def load_topics() -> list:
    """
    Load all topics from the JSON data file and return them as Topic objects.

    If the file does not exist (first run), returns an empty list so the
    application starts cleanly without crashing. If the file is corrupted
    or malformed, prints a warning and returns an empty list.

    Returns:
        list: Ordered list of Topic objects restored from disk.
              Returns an empty list if no data file exists yet.

    Raises:
        No exceptions are propagated — all errors are caught and reported
        as warnings so the program can always start successfully.
    """
    _ensure_data_dir()

    # No data file yet — first run
    if not os.path.exists(_DATA_FILE):
        return []

    try:
        with open(_DATA_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)
        return [Topic.from_dict(entry) for entry in raw]

    except (json.JSONDecodeError, KeyError, TypeError) as err:
        print(f"\n  Warning: Could not read data file ({err}).")
        print("  Starting with no topics. Previous data may be lost.\n")
        return []


def save_topics(topics: list) -> None:
    """
    Serialise all topics and write them to the JSON data file.

    Overwrites the existing file completely with the current in-memory state.
    The file is written with 2-space indentation so it is human-readable
    if opened in a text editor.

    Args:
        topics (list): Full list of Topic objects to persist to disk.

    Raises:
        OSError: If the file cannot be written (e.g. permissions error).
                 Propagated to the caller so the user is notified.
    """
    _ensure_data_dir()

    data = [topic.to_dict() for topic in topics]

    with open(_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
