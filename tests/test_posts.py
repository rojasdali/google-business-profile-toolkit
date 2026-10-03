"""Tests for local posts publishing and payload generation."""

import tempfile

import pytest

from gbp_toolkit.client import GBPClient
from gbp_toolkit.dedup import PostDeduplicationLedger
from gbp_toolkit.posts import PostsService, build_post_payload
from gbp_toolkit.types import CallToAction, LocalPostPayload, PostActionType, PostTopicType


def test_build_post_payload():
    cta = CallToAction(action_type=PostActionType.LEARN_MORE, url="https://wa.me/17868038622")
    payload = LocalPostPayload(
        summary="Prueba de actualización",
        language_code="es",
        topic_type=PostTopicType.STANDARD,
        call_to_action=cta,
    )
    data = build_post_payload(payload)
    assert data["languageCode"] == "es"
    assert data["summary"] == "Prueba de actualización"
    assert data["callToAction"]["actionType"] == "LEARN_MORE"
    assert data["callToAction"]["url"] == "https://wa.me/17868038622"


def test_post_exceeding_character_limit():
    long_text = "a" * 1501
    payload = LocalPostPayload(summary=long_text)
    with pytest.raises(ValueError, match="exceeds Google 1500-char limit"):
        build_post_payload(payload)


def test_dry_run_post_publishing():
    with tempfile.NamedTemporaryFile(suffix=".json") as tmp:
        ledger = PostDeduplicationLedger(ledger_path=tmp.name)
        client = GBPClient(
            client_id="test",
            client_secret="test",
            refresh_token="test",
            location_id="locations/123",
            dry_run=True,
        )
        posts_svc = PostsService(client, ledger=ledger)

        res = posts_svc.publish(
            summary="Servicio Wash & Fold en Hialeah",
            topic_slug="wash-fold-promo",
            cta_url="https://wa.me/17868038622",
        )
        assert res.state == "SIMULATED"
        assert res.summary == "Servicio Wash & Fold en Hialeah"
