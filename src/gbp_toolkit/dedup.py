"""Deduplication ledger engine ensuring zero repetitive Google Business Profile posts."""

import hashlib
import json
import os
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional


def normalize_post_text(text: str) -> str:
    """Normalizes post text for consistent hashing (lowercase, strip whitespace and punctuation)."""
    cleaned = re.sub(r"[^\w\s]", "", text.lower())
    return " ".join(cleaned.split())


def compute_post_hash(text: str) -> str:
    """Computes a stable SHA-256 hash of normalized post text."""
    norm = normalize_post_text(text)
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()[:16]


class PostDeduplicationLedger:
    """Tracks published Google Business Profile posts to enforce zero-repeat cooldowns."""

    def __init__(self, ledger_path: str = "data/processed/gbp_posts_history.json", cooldown_days: int = 90):
        self.ledger_path = ledger_path
        self.cooldown_days = cooldown_days
        self._history: List[Dict[str, Any]] = self._load()

    def _load(self) -> List[Dict[str, Any]]:
        if os.path.exists(self.ledger_path):
            try:
                with open(self.ledger_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def _save(self) -> None:
        os.makedirs(os.path.dirname(os.path.abspath(self.ledger_path)), exist_ok=True)
        with open(self.ledger_path, "w", encoding="utf-8") as f:
            json.dump(self._history, f, indent=2, ensure_ascii=False)

    def is_duplicate(self, text: str, topic_slug: Optional[str] = None) -> bool:
        """Returns True if the content or topic slug was published within the cooldown window."""
        post_hash = compute_post_hash(text)
        cutoff = datetime.now() - timedelta(days=self.cooldown_days)

        for entry in self._history:
            pub_date = datetime.fromisoformat(entry.get("published_at", "1970-01-01"))
            if pub_date >= cutoff:
                if entry.get("post_hash") == post_hash:
                    return True
                if topic_slug and entry.get("topic_slug") == topic_slug:
                    return True
        return False

    def record_publication(self, text: str, topic_slug: str, post_id: str = "") -> None:
        """Appends a published post entry to the persistent ledger."""
        entry = {
            "post_hash": compute_post_hash(text),
            "topic_slug": topic_slug,
            "post_id": post_id,
            "published_at": datetime.now().isoformat(),
            "summary_preview": text[:80] + ("..." if len(text) > 80 else ""),
        }
        self._history.append(entry)
        self._save()
