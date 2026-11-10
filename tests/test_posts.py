"""Tests for local posts publishing, policy linting, and rejection auditing."""

import tempfile
from unittest.mock import MagicMock

import pytest

from gbp_toolkit.client import GBPClient
from gbp_toolkit.dedup import PostDeduplicationLedger
from gbp_toolkit.posts import PostsService, build_post_payload, validate_post_policy
from gbp_toolkit.types import CallToAction, LocalPostPayload, PostActionType, PostTopicType


def test_build_post_payload_link_cta():
    cta = CallToAction(action_type=PostActionType.LEARN_MORE, url="https://wa.me/15550109999")
    payload = LocalPostPayload(
        summary="Prueba de actualización",
        language_code="es",
        topic_type=PostTopicType.STANDARD,
        call_to_action=cta,
    )
    data = build_post_payload(payload)
    assert data["languageCode"] == "es"
    assert data["summary"] == "Prueba de actualización"
    assert data["callToAction"] == {"actionType": "LEARN_MORE", "url": "https://wa.me/15550109999"}


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
            summary="Servicio Wash & Fold en FL con atención VIP y acceso ADA",
            topic_slug="wash-fold-promo",
            cta_url="https://wa.me/15550109999",
        )
        assert res.state == "SIMULATED"


def test_validate_post_policy_detects_urls_phones_shouting_and_link_warnings():
    clean = validate_post_policy("Especial de lavado y doblado en FL con trato VIP y rampa ADA.", cta_type="CALL")
    assert clean.valid is True
    assert clean.ok is True
    assert clean.violations == []
    assert clean.warnings == []

    warn_link = validate_post_policy("Especial de lavado y doblado a domicilio.", cta_type="LEARN_MORE")
    assert warn_link.valid is True
    assert len(warn_link.warnings) == 1
    assert "LEARN_MORE" in warn_link.warnings[0]

    bad_url = validate_post_policy("Escríbenos en https://wa.me/15550109999 hoy", cta_type="CALL")
    assert bad_url.valid is False
    assert any("Raw URL" in v for v in bad_url.violations)

    bad_phone = validate_post_policy("Llámanos al (555) 234-5678 para precios", cta_type="CALL")
    assert bad_phone.valid is False
    assert any("Phone number" in v for v in bad_phone.violations)

    bad_caps = validate_post_policy("SERVICIOS & PRECIOS disponibles hoy", cta_type="CALL")
    assert bad_caps.valid is False
    assert any("SERVICIOS" in v for v in bad_caps.violations)


def test_publish_enforces_policy_by_default():
    with tempfile.NamedTemporaryFile(suffix=".json") as tmp:
        ledger = PostDeduplicationLedger(ledger_path=tmp.name)
        mock_client = MagicMock(spec=GBPClient)
        mock_client.account_id = "accounts/111"
        mock_client.location_id = "locations/222"
        mock_client.dry_run = True
        posts_svc = PostsService(mock_client, ledger=ledger)
        with pytest.raises(ValueError, match="GBP post policy violation"):
            posts_svc.publish(summary="PROMOCION GRATIS al 555-234-5678", cta_type="CALL")


def test_list_posts_and_audit_rejected_posts():
    mock_client = MagicMock(spec=GBPClient)
    mock_client.account_id = "accounts/111"
    mock_client.location_id = "locations/222"
    mock_client.dry_run = False
    mock_client.request.return_value = {
        "localPosts": [
            {
                "name": "accounts/111/locations/222/localPosts/p1",
                "state": "LIVE",
                "topicType": "STANDARD",
                "callToAction": {"actionType": "CALL"},
                "summary": "Ropa limpia y doblada hoy.",
                "media": [{"mediaFormat": "PHOTO"}],
                "createTime": "2026-11-10T19:00:00Z",
            },
            {
                "name": "accounts/111/locations/222/localPosts/p2",
                "state": "REJECTED",
                "topicType": "STANDARD",
                "callToAction": {"actionType": "LEARN_MORE", "url": "https://wa.me/15550109999"},
                "summary": "SERVICIOS & PRECIOS de lavandería",
                "createTime": "2026-10-05T18:00:00Z",
            },
        ]
    }
    svc = PostsService(mock_client)
    audit = svc.audit_rejected_posts(page_size=20)
    assert audit["total"] == 2
    assert audit["liveCount"] == 1
    assert audit["rejectedCount"] == 1
    assert audit["rejectionRate"] == 0.5
    rejected = audit["rejectedPosts"][0]
    assert rejected["post_id"] == "p2"
    assert any("ALL-CAPS" in ind for ind in rejected["rejectionIndicators"])
    assert any("wa.me" in ind for ind in rejected["rejectionIndicators"])
