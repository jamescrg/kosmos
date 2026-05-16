"""Tests for the Filter-button indicator coherence on the Invoices list.

The invoices page already has a status quick-filter row + a Filter modal.
The page-level filter_active flag was already computed correctly (excludes
status and order_by); the gap fixed here is the modal POST handler stuffing
csrfmiddlewaretoken into the session and overwriting the dict instead of
merging with the prior quick-filter selection.
"""

import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


def _session_for(client, key):
    return client.session.get(key, {})


def test_default_state_filter_button_off(client):
    response = client.get(reverse("invoicing:invoices-index"))
    assert response.status_code == 200
    assert response.context["filter_active"] in (False, None, {})


def test_status_quick_filter_does_not_light_filter_button(client):
    client.post(reverse("invoicing:invoices-filter-status", args=["DRAFT"]))
    response = client.get(reverse("invoicing:invoices-index"))
    # status has its own button row; filter_active deliberately excludes it.
    assert response.context["filter_active"] in (False, None, {})
    assert response.context["selected_status"] == "DRAFT"


def test_modal_with_matter_lights_filter_button(client):
    # Pass a matter value (no real matter required — filter just needs the field set).
    client.post(reverse("invoicing:invoices-filter"), {"matter": "1"})
    response = client.get(reverse("invoicing:invoices-index"))
    assert response.context["filter_active"]


def test_modal_apply_strips_csrf_token_from_session(client):
    client.post(reverse("invoicing:invoices-filter"), {"matter": "1"})
    session_filter = _session_for(client, "invoices_filter")
    assert "csrfmiddlewaretoken" not in session_filter


def test_modal_apply_preserves_quick_filter_status(client):
    # Set status via the quick-filter buttons first.
    client.post(reverse("invoicing:invoices-filter-status", args=["DRAFT"]))
    pre = _session_for(client, "invoices_filter")
    assert pre.get("status") == "DRAFT"

    # Apply the modal with just a matter — status not in the POST.
    client.post(reverse("invoicing:invoices-filter"), {"matter": "1"})
    post = _session_for(client, "invoices_filter")
    # Merge preserves the quick-filter status selection.
    assert post.get("status") == "DRAFT"
    assert post.get("matter") == "1"
