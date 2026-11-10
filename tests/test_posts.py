"""Tests for local posts publishing and payload generation."""

import tempfile
from unittest.mock import MagicMock

import pytest

from gbp_toolkit.client import GBPClient
from gbp_toolkit.dedup import PostDeduplicationLedger
from gbp_toolkit.posts import PostsService, build_post_payload
from gbp_toolkit.types import CallToAction, LocalPostPayload, PostActionType, PostTopicType


def test_build_post_payload_link_cta():
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
    assert data["callToAction"] == {"actionType": "LEARN_MORE", "url": "https://wa.me/17868038622"}


def test_build_post_payload_call_cta_omits_url():
    cta = CallToAction(action_type=PostActionType.CALL, url="https://should-be-dropped.example.com")
    payload = LocalPostPayload(summary="Llámanos hoy", call_to_action=cta)
    data = build_post_payload(payload)
    assert data["callToAction"] == {"actionType": "CALL"}
    assert "url" not in data["callToAction"]


def test_publish_call_cta_without_url():
    with tempfile.NamedTemporaryFile(suffix=".json") as tmp:
        ledger = PostDeduplicationLedger(ledger_path=tmp.name)
        mock_client = MagicMock(spec=GBPClient)
        mock_client.account_id = "accounts/111"
        mock_client.location_id = "locations/222"
        mock_client.dry_run = False
        mock_client.request.return_value = {"name": "accounts/111/locations/222/localPosts/999", "state": "LIVE"}

        posts_svc = PostsService(mock_client, ledger=ledger)
        res = posts_svc.publish(summary="Llámanos para Wash & Fold", topic_slug="call-cta", cta_type="CALL")
        assert res.state == "LIVE"
        sent_body = mock_client.request.call_args.kwargs["json_data"]
        assert sent_body["callToAction"] == {"actionType": "CALL"}
        assert "url" not in sent_body["callToAction"]


def test_post_exceeding_character_limit():
    payload = LocalPostPayload(summary="a" * 1501)
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
