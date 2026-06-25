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
        # The concrete LawPay/AffiniPay adapter is built against sandbox keys
        # in a later step; fail loudly until then.
        raise ProcessorConfigError(
            "The 'lawpay' processor is not implemented yet. "
            "Set PAYMENT_PROCESSOR=fake until the LawPay adapter is built."
        )

    raise ProcessorConfigError(f"Unknown PAYMENT_PROCESSOR: {name!r}")
