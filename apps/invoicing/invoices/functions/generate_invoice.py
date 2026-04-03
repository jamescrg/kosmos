import os
from tempfile import NamedTemporaryFile

from django.core.files.base import ContentFile
from django.core.handlers.wsgi import WSGIRequest
from django.template.loader import render_to_string
from weasyprint import HTML

from apps.activity.expenses.models import ExpenseEntry
from apps.activity.time.models import TimeEntry
from apps.invoicing.invoices.models import Invoice
from apps.settings.models import Company
from apps.trust.trust import get_confirmed_client_balance


def generate_invoice(
    invoice: Invoice, request: WSGIRequest = None, *, base_url: str = ""
) -> NamedTemporaryFile:
    """
    Generate a PDF invoice for the given invoice instance.

    Either request or base_url must be provided for resolving static file paths.
    """

    if invoice.show_comp:
        time_entries = TimeEntry.objects.filter(
            invoice=invoice,
        ).order_by("date")
        expenses = ExpenseEntry.objects.filter(
            invoice=invoice,
        ).order_by("date")
    else:
        time_entries = TimeEntry.objects.filter(
            invoice=invoice,
            comp=invoice.show_comp,
        ).order_by("date")
        expenses = ExpenseEntry.objects.filter(
            invoice=invoice,
            comp=invoice.show_comp,
        ).order_by("date")

    # Get confirmed trust balance for the client
    confirmed_balance = 0
    if invoice.matter.client:
        confirmed_balance = get_confirmed_client_balance(invoice.matter.client.id)

    context = {
        "invoice": invoice,
        "time_entries": time_entries,
        "expenses": expenses,
        "confirmed_balance": confirmed_balance,
        "company": Company.objects.first(),
    }

    html_string = render_to_string("invoicing/invoices/invoice.html", context)
    if not base_url and request:
        base_url = request.build_absolute_uri("/").rstrip("/")
    html = HTML(string=html_string, base_url=base_url)

    with NamedTemporaryFile(suffix=".pdf", delete=False) as pdf_file:
        html.write_pdf(target=pdf_file.name)
        pdf_file.seek(0)

    return pdf_file


def store_invoice_pdf(
    invoice: Invoice, request: WSGIRequest = None, *, base_url: str = ""
) -> None:
    """Generate PDF and store it in the invoice's pdf_file field."""
    pdf_file = generate_invoice(invoice, request, base_url=base_url)

    with open(pdf_file.name, "rb") as f:
        pdf_content = f.read()

    os.unlink(pdf_file.name)

    filename = f"invoice_{invoice.id}.pdf"

    if invoice.pdf_file:
        invoice.pdf_file.delete(save=False)

    invoice.pdf_file.save(filename, ContentFile(pdf_content), save=False)
    Invoice.objects.filter(pk=invoice.pk).update(pdf_file=invoice.pdf_file)
