"""Build public payment links for an invoice."""

from django.conf import settings
from django.urls import reverse

from utils.signing import make_balance_token, make_payment_token


def _absolute(path, request):
    if request is not None:
        return request.build_absolute_uri(path)
    base = (getattr(settings, "PUBLIC_BASE_URL", "") or "").rstrip("/")
    return f"{base}{path}" if base else path


def payment_path(invoice) -> str:
    """Root-relative payment URL, e.g. /pay/<signed-token>/."""
    return reverse("pay:invoice", kwargs={"token": make_payment_token(invoice)})


def payment_url(invoice, request=None) -> str:
    """Absolute payment URL for emails / off-request contexts.

    Uses the request host when available, else settings.PUBLIC_BASE_URL.
    """
    return _absolute(payment_path(invoice), request)


def balance_payment_path(matter) -> str:
    """Root-relative catch-up (full-balance) payment URL for a matter."""
    return reverse("pay:balance", kwargs={"token": make_balance_token(matter)})


def balance_payment_url(matter, request=None) -> str:
    """Absolute matter-balance payment URL (see payment_url)."""
    return _absolute(balance_payment_path(matter), request)
