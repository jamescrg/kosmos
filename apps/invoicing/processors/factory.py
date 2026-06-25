"""Select the active payment processor from settings.

    PAYMENT_PROCESSOR = "fake"   # or "lawpay"

The default is "fake" so dev/CI and the test suite run without any processor
credentials. The real `LawPayProcessor` is registered here once it exists.
"""

from django.conf import settings

from .base import PaymentProcessor, ProcessorConfigError
from .fake import FakeProcessor


def get_processor(name: str | None = None) -> PaymentProcessor:
    """Return an instance of the configured (or named) processor."""
    name = name or getattr(settings, "PAYMENT_PROCESSOR", "fake")

    if name == "fake":
        return FakeProcessor()

    if name == "lawpay":
        # Imported lazily so the package needn't import `requests` unless the
        # LawPay processor is actually selected.
        from .lawpay import LawPayProcessor

        return LawPayProcessor()

    raise ProcessorConfigError(f"Unknown PAYMENT_PROCESSOR: {name!r}")
