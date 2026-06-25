"""Pluggable payment-processor abstraction for online invoice collection.

The rest of the app talks to a `PaymentProcessor` through the normalized value
objects in `base` and never sees a concrete processor's specifics. Select the
active processor with `get_processor()`.

    from apps.invoicing.processors import get_processor
    processor = get_processor()
    result = processor.charge(token=tok, amount_cents=10000,
                              reference=f"invoice:{invoice.id}", method=CARD)
"""

from .base import (
    BANK,
    CARD,
    FAILED,
    PENDING,
    REFUNDED,
    RETURNED,
    SUCCEEDED,
    VOIDED,
    ChargeError,
    ChargeResult,
    ClientConfig,
    PaymentError,
    PaymentProcessor,
    ProcessorConfigError,
    WebhookEvent,
    WebhookVerificationError,
)
from .factory import get_processor

__all__ = [
    "BANK",
    "CARD",
    "FAILED",
    "PENDING",
    "REFUNDED",
    "RETURNED",
    "SUCCEEDED",
    "VOIDED",
    "ChargeError",
    "ChargeResult",
    "ClientConfig",
    "PaymentError",
    "PaymentProcessor",
    "ProcessorConfigError",
    "WebhookEvent",
    "WebhookVerificationError",
    "get_processor",
]
