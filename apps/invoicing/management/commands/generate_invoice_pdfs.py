"""
Generate and store PDFs for all existing invoices that don't have one.

Usage:
    python manage.py generate_invoice_pdfs
    python manage.py generate_invoice_pdfs --base-url http://localhost:8000
    python manage.py generate_invoice_pdfs --overwrite  # regenerate all PDFs
"""

from django.conf import settings
from django.core.management.base import BaseCommand

from apps.invoicing.invoices.functions.generate_invoice import store_invoice_pdf
from apps.invoicing.invoices.models import Invoice


class Command(BaseCommand):
    help = "Generate and store PDFs for existing invoices"

    def add_arguments(self, parser):
        parser.add_argument(
            "--base-url",
            default=f"file://{settings.BASE_DIR}",
            help="Base URL for resolving static files (default: file:// path)",
        )
        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="Regenerate PDFs even for invoices that already have one",
        )

    def handle(self, *args, **options):
        base_url = options["base_url"]
        overwrite = options["overwrite"]

        invoices = Invoice.objects.exclude(status="VOID").select_related("matter")

        if not overwrite:
            invoices = invoices.filter(pdf_file="")

        total = invoices.count()

        if total == 0:
            self.stdout.write("No invoices need PDF generation.")
            return

        self.stdout.write(f"Generating PDFs for {total} invoices...")

        success = 0
        errors = 0

        for i, invoice in enumerate(invoices.iterator(), 1):
            try:
                store_invoice_pdf(invoice, base_url=base_url)
                success += 1
                if i % 10 == 0:
                    self.stdout.write(f"  {i}/{total} processed...")
            except Exception as e:
                errors += 1
                self.stderr.write(f"  Error on Invoice #{invoice.id}: {e}")

        self.stdout.write(
            self.style.SUCCESS(f"Done. {success} PDFs generated, {errors} errors.")
        )
