"""
topic.py
--------
Defines the Topic and ReviewSession classes used throughout MemoryMate.

Each Topic tracks its name, subject, and a chronological list of
ReviewSession objects. ReviewSessions store the date, confidence
rating, and resulting stability value for each study session logged.

Classes:
    ReviewSession  -- A single logged study session.
    Topic          -- A study topic with full review history.
"""

from datetime import date, datetime


class ReviewSession:
    """
    Represents a single study session logged by the user.

    Attributes:
        date (str)        : Date of the session in YYYY-MM-DD format.
        confidence (int)  : User self-rating from 1 (forgot) to 5 (perfect).
        stability (float) : Memory stability value computed after this session.
    """

    def __init__(self, date_str: str, confidence: int, stability: float) -> None:
        """
        Initialise a ReviewSession.

        Args:
            date_str (str)    : Review date as 'YYYY-MM-DD'.
            confidence (int)  : Confidence rating between 1 and 5.
            stability (float) : Stability value calculated after this review.
        """
        self.date = date_str
        self.confidence = confidence
        self.stability = stability

    def to_dict(self) -> dict:
        """
        Serialise this session to a dictionary for JSON storage.

        Returns:
            dict: Keys 'date', 'confidence', 'stability'.
        """
        return {
            "date": self.date,
            "confidence": self.confidence,
            "stability": self.stability,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ReviewSession":
        """
        Reconstruct a ReviewSession from a dictionary (loaded from JSON).

        Args:
            data (dict): Must contain 'date', 'confidence', 'stability'.

        Returns:
            ReviewSession: Restored session object.
        """
        return cls(data["date"], data["confidence"], data["stability"])

    def __repr__(self) -> str:
        return (
            f"ReviewSession(date='{self.date}', "
            f"confidence={self.confidence}, "
            f"stability={self.stability:.3f})"
        )


class Topic:
    """
    Represents a single study topic tracked by MemoryMate.

    Each topic holds a name, subject category, the date it was added,
    and an ordered list of ReviewSession objects. The initial stability
    value of 1.0 means the first review is recommended within ~1 day.

    Class attributes:
        INITIAL_STABILITY (float): Starting stability for all new topics.

    Attributes:
        name (str)               : Display name of the topic.
        subject (str)            : Subject or course category.
        date_added (str)         : Date topic was added in YYYY-MM-DD format.
        review_history (list)    : Chronological list of ReviewSession objects.
    """

    INITIAL_STABILITY = 1.0

    def __init__(self, name: str, subject: str, date_added: str = None) -> None:
        """
        Initialise a new Topic.

        Args:
            name (str)              : Name of the topic (e.g. 'Binary Trees').
            subject (str)           : Subject/category (e.g. 'COMP9001').
            date_added (str, opt)   : Date added as 'YYYY-MM-DD'. Defaults to today.
        """
        self.name = name
        self.subject = subject
        self.date_added = date_added or str(date.today())
        self.review_history = []

    def add_review(self, confidence: int, new_stability: float) -> None:
        """
        Append a new ReviewSession to this topic's history.

        Args:
            confidence (int)       : User's confidence rating from 1 to 5.
            new_stability (float)  : Updated stability after this review.
        """
        session = ReviewSession(str(date.today()), confidence, new_stability)
        self.review_history.append(session)

    def days_since_last_review(self) -> float:
        """
        Compute the number of days elapsed since the last review.

        If the topic has never been reviewed, returns days since it was added.

        Returns:
            float: Days since the most recent review (or since topic was added).
        """
        if not self.review_history:
            reference = datetime.strptime(self.date_added, "%Y-%m-%d").date()
        else:
            reference = datetime.strptime(
                self.review_history[-1].date, "%Y-%m-%d"
            ).date()
        return (date.today() - reference).days

    def current_stability(self) -> float:
        """
        Return the most recent stability value for this topic.

        Returns:
            float: Last recorded stability, or INITIAL_STABILITY if never reviewed.
        """
        if not self.review_history:
            return self.INITIAL_STABILITY
        return self.review_history[-1].stability

    def to_dict(self) -> dict:
        """
        Serialise this topic to a dictionary for JSON storage.

        Returns:
            dict: Full representation including review history.
        """
        return {
            "name": self.name,
            "subject": self.subject,
            "date_added": self.date_added,
            "review_history": [s.to_dict() for s in self.review_history],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Topic":
        """
        Reconstruct a Topic from a dictionary (loaded from JSON).

        Args:
            data (dict): Must contain 'name', 'subject', 'date_added',
                         and 'review_history'.

        Returns:
            Topic: Restored topic object with full history.
        """
        topic = cls(data["name"], data["subject"], data["date_added"])
        topic.review_history = [
            ReviewSession.from_dict(s) for s in data.get("review_history", [])
        ]
        return topic

    def __repr__(self) -> str:
        return f"Topic(name='{self.name}', subject='{self.subject}')"
