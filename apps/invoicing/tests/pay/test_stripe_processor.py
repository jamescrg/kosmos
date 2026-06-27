from types import SimpleNamespace
from unittest.mock import patch

import pytest
import stripe

from apps.invoicing.processors.base import (
    BANK,
    CARD,
    FAILED,
    PENDING,
    REFUNDED,
    SUCCEEDED,
    ChargeError,
    ProcessorConfigError,
    WebhookVerificationError,
)
from apps.invoicing.processors.stripe import StripeProcessor


def proc():
    return StripeProcessor(
        secret_key="sk_test_x", publishable_key="pk_test_x", webhook_secret="whsec_x"
    )


def test_requires_secret_key():
    with pytest.raises(ProcessorConfigError):
        StripeProcessor(secret_key="", publishable_key="", webhook_secret="")


def test_factory_returns_stripe(settings):
    settings.STRIPE_SECRET_KEY = "sk_test"
    settings.STRIPE_PUBLISHABLE_KEY = "pk_test"
    settings.STRIPE_WEBHOOK_SECRET = "whsec"
    from apps.invoicing.processors import get_processor

    assert isinstance(get_processor("stripe"), StripeProcessor)


def test_charge_success_card():
    pi = {
        "id": "pi_1",
        "status": "succeeded",
        "amount": 5000,
        "payment_method_types": ["card"],
    }
    with patch("stripe.PaymentIntent.create", return_value=pi) as m:
        r = proc().charge(
            token="pm_1",
            amount_cents=5000,
            reference="invoice:1",
            method="card",
            idempotency_key="invoice:1",
        )
    assert r.status == SUCCEEDED and r.accepted and r.transaction_id == "pi_1"
    assert r.method == CARD
    kw = m.call_args.kwargs
    assert kw["api_key"] == "sk_test_x"
    assert kw["idempotency_key"] == "invoice:1"
    assert kw["confirm"] is True
    assert kw["payment_method"] == "pm_1"


def test_charge_processing_is_pending_bank():
    pi = {
        "id": "pi_2",
        "status": "processing",
        "amount": 5000,
        "payment_method_types": ["us_bank_account"],
    }
    with patch("stripe.PaymentIntent.create", return_value=pi):
        r = proc().charge(token="pm", amount_cents=5000, reference="r", method="bank")
    assert r.status == PENDING and r.is_pending and r.method == BANK


def test_charge_card_declined():
    err = stripe.CardError(
        "Your card was declined.", param="number", code="card_declined"
    )
    with patch("stripe.PaymentIntent.create", side_effect=err):
        with pytest.raises(ChargeError) as ei:
            proc().charge(token="pm", amount_cents=5000, reference="r", method="card")
    assert ei.value.code == "card_declined"


def test_charge_requires_action_rejected():
    pi = {
        "id": "pi",
        "status": "requires_action",
        "amount": 5000,
        "payment_method_types": ["card"],
    }
    with patch("stripe.PaymentIntent.create", return_value=pi):
        with pytest.raises(ChargeError) as ei:
            proc().charge(token="pm", amount_cents=5000, reference="r", method="card")
    assert ei.value.code == "requires_action"


def test_fetch_transaction():
    pi = {
        "id": "pi_9",
        "status": "succeeded",
        "amount": 1234,
        "payment_method_types": ["card"],
    }
    with patch("stripe.PaymentIntent.retrieve", return_value=pi):
        r = proc().fetch_transaction("pi_9")
    assert (
        r.transaction_id == "pi_9" and r.amount_cents == 1234 and r.status == SUCCEEDED
    )


def test_refund_calls_stripe_and_returns_state():
    pi = {
        "id": "pi_r",
        "status": "succeeded",
        "amount": 5000,
        "payment_method_types": ["card"],
    }
    with (
        patch("stripe.Refund.create") as mr,
        patch("stripe.PaymentIntent.retrieve", return_value=pi),
    ):
        proc().refund(transaction_id="pi_r", amount_cents=5000)
    mr.assert_called_once()
    assert mr.call_args.kwargs["payment_intent"] == "pi_r"
    assert mr.call_args.kwargs["amount"] == 5000


def test_webhook_payment_intent_succeeded():
    event = {
        "id": "evt_1",
        "type": "payment_intent.succeeded",
        "data": {"object": {"object": "payment_intent", "id": "pi_1", "amount": 5000}},
    }
    with patch("stripe.Webhook.construct_event", return_value=event):
        ev = proc().verify_and_parse_webhook(
            SimpleNamespace(body=b"{}", signature="sig")
        )
    assert (
        ev.status == SUCCEEDED
        and ev.transaction_id == "pi_1"
        and ev.amount_cents == 5000
    )


@pytest.mark.parametrize(
    "etype,expected",
    [
        ("payment_intent.payment_failed", FAILED),
        ("payment_intent.processing", PENDING),
    ],
)
def test_webhook_pi_statuses(etype, expected):
    event = {
        "id": "evt",
        "type": etype,
        "data": {"object": {"object": "payment_intent", "id": "pi_x", "amount": 100}},
    }
    with patch("stripe.Webhook.construct_event", return_value=event):
        ev = proc().verify_and_parse_webhook(SimpleNamespace(body=b"{}", signature="s"))
    assert ev.status == expected and ev.transaction_id == "pi_x"


def test_webhook_charge_refunded_resolves_payment_intent():
    event = {
        "id": "evt",
        "type": "charge.refunded",
        "data": {
            "object": {
                "object": "charge",
                "id": "ch_1",
                "payment_intent": "pi_1",
                "amount": 5000,
            }
        },
    }
    with patch("stripe.Webhook.construct_event", return_value=event):
        ev = proc().verify_and_parse_webhook(SimpleNamespace(body=b"{}", signature="s"))
    assert ev.status == REFUNDED and ev.transaction_id == "pi_1"


def test_webhook_bad_signature():
    with patch(
        "stripe.Webhook.construct_event",
        side_effect=stripe.SignatureVerificationError("bad", "sig_header"),
    ):
        with pytest.raises(WebhookVerificationError):
            proc().verify_and_parse_webhook(SimpleNamespace(body=b"{}", signature="x"))


def test_webhook_unhandled_event_ignored():
    event = {"id": "e", "type": "customer.created", "data": {"object": {}}}
    with patch("stripe.Webhook.construct_event", return_value=event):
        with pytest.raises(WebhookVerificationError):
            proc().verify_and_parse_webhook(SimpleNamespace(body=b"{}", signature="x"))
