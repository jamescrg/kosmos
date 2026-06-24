from datetime import datetime

from django.core.management.base import BaseCommand

import apps.calendar.google as google
from apps.calendar import sync


class Command(BaseCommand):
    help = "Sync events with Google Calendar (two-way sync)"

    def handle(self, *args, **options):
        self.stdout.write("Starting Google Calendar sync...")

        try:
            # Push local changes + drain queued deletions first, so local
            # removals reach Google before the pull (which would otherwise
            # re-create them) and any previously failed pushes get retried.
            summary = sync.reconcile()
            self.stdout.write(f"Reconciled local changes: {summary}")

            google.sync_from_google()
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.stdout.write(
                self.style.SUCCESS(
                    f"✓ Google Calendar sync completed successfully at {timestamp}"
                )
            )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Sync failed: {e}"))
            raise
