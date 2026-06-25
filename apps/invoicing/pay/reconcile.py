"""Reconcile processor webhook events against recorded payments.

Runs out-of-band (via Django-Q `async_task`, or inline as a fallback). The
processor's `verify_and_parse_webhook` does NOT trust the posted body — it
re-fetches the transaction from the API and reports the authoritative status —
so this module acts on a confirmed `WebhookEvent`.

The critical case is ACH: a charge that looked accepted can **return** or
**fail** days later. We then unapply the payment (reverting the invoice to
unpaid via the existing `PaymentApplication.delete()` hook), drop the phantom
payment, and email staff.
"""

import logging
from types import SimpleNamespace

from django.core.mail import mail_admins

from apps.invoicing.invoices.models import Invoice
from apps.invoicing.payments.models import Payment
from apps.invoicing.processors import REVERSED_STATUSES, PaymentError, get_processor

logger = logging.getLogger(__name__)


def reconcile_webhook(processor_name, body):
    """Verify and apply a single webhook delivery. Safe to call from a task."""
    try:
        processor = get_processor(processor_name)
    except PaymentError:
        logger.warning("Webhook for unknown processor %r ignored", processor_name)
        return
    raw = body.encode() if isinstance(body, str) else body
    try:
        event = processor.verify_and_parse_webhook(SimpleNamespace(body=raw))
    except PaymentError as exc:
        logger.warning("Unverifiable %s webhook ignored: %s", processor_name, exc)
        return
    _apply_event(event)


def _apply_event(event):
    payment = Payment.objects.filter(
        processor=event.processor, processor_txn_id=event.transaction_id
    ).first()
    if payment is None:
        return  # not a charge we recorded (or already reversed) — nothing to do
    if payment.processor_status == event.status:
        return  # idempotent: webhook re-delivery, already in this state

    if event.status in REVERSED_STATUSES:
        _reverse(payment, event)
    else:
        payment.processor_status = event.status
        payment.save(update_fields=["processor_status"])


def _reverse(payment, event):
    """An accepted charge fell through (ACH return / NSF / void)."""
    invoice_ids = list(payment.applications.values_list("invoice_id", flat=True))
    # Delete each application individually so PaymentApplication.delete() runs
    # (records history; a cascade delete would skip the hook).
    for application in list(payment.applications.all()):
        application.delete()
    detail = payment.detail
    payment.delete()

    # The delete hook leaves an invoice PAID when its *last* allocation is removed
    # (a legacy amount_remaining rule counts PAID + no-allocations as fully paid).
    # Explicitly revert any such invoice so a returned payment shows as unpaid —
    # but leave PAID any invoice still fully covered by other allocations.
    for inv_id in invoice_ids:
        inv = Invoice.objects.filter(pk=inv_id).first()
        if inv is None or inv.status != "PAID":
            continue
        has_alloc = inv.applications.exists() or inv.credit_applications.exists()
        if not has_alloc or inv.amount_remaining > 0:
            inv.status = "SENT"
            inv.save(update_fields=["status"])

    mail_admins(
        subject=f"Online payment {event.status}: {event.transaction_id}",
        message=(
            f"A previously-accepted online payment has {event.status}.\n\n"
            f"{detail}\n"
            f"Affected invoice id(s): {invoice_ids}\n\n"
            "The invoice has been reverted to unpaid. Please follow up with the "
            "client."
        ),
        fail_silently=True,
    )
    logger.warning(
        "Reversed online payment %s (%s); invoices %s reverted",
        event.transaction_id,
        event.status,
        invoice_ids,
    )
