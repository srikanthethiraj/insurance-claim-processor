"""Feedback Mechanism for the Insurance Claim Processor."""

from datetime import datetime, timezone

from src.models import FeedbackEntry


class FeedbackMechanism:
    """Collects user ratings and comments on processing results."""

    def __init__(self) -> None:
        self._store: dict[str, list[FeedbackEntry]] = {}

    def submit(self, summary_id: str, rating: int, comment: str = "") -> None:
        """Store feedback. Rating must be 1-5, raises ValueError otherwise."""
        if not isinstance(rating, int) or rating < 1 or rating > 5:
            raise ValueError(f"Rating must be between 1 and 5, got {rating}")

        entry = FeedbackEntry(
            summary_id=summary_id,
            rating=rating,
            comment=comment,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        self._store.setdefault(summary_id, []).append(entry)

    def get_feedback(self, summary_id: str) -> list[FeedbackEntry]:
        """Retrieve all feedback for a given summary."""
        return list(self._store.get(summary_id, []))
