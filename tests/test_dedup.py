"""Tests for post deduplication engine."""

import tempfile

from gbp_toolkit.dedup import PostDeduplicationLedger, compute_post_hash, normalize_post_text


def test_normalize_post_text():
    raw1 = "  🧺 ¡Especial Wash & Fold esta semana! 📞 (786) 803-8622  "
    raw2 = "especial wash fold esta semana 786 8038622"
    assert normalize_post_text(raw1) == normalize_post_text(raw2)


def test_compute_post_hash():
    h1 = compute_post_hash("Lava tus edredones King Size")
    h2 = compute_post_hash("  lava tus   edredones king size!  ")
    assert h1 == h2


def test_dedup_ledger_cooldown():
    with tempfile.NamedTemporaryFile(suffix=".json") as tmp:
        ledger = PostDeduplicationLedger(ledger_path=tmp.name, cooldown_days=90)
        text = "Especial de mitad de semana a solo $1.00 por libra"

        assert not ledger.is_duplicate(text, topic_slug="midweek-promo")
        ledger.record_publication(text, topic_slug="midweek-promo", post_id="post_123")

        # Now it must be rejected as duplicate
        assert ledger.is_duplicate(text, topic_slug="midweek-promo")
        assert ledger.is_duplicate("Different copy", topic_slug="midweek-promo")
        assert not ledger.is_duplicate("Brand new topic and copy", topic_slug="comforters-weekend")
