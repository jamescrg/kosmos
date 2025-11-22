from django.core.management.base import BaseCommand

import apps.agenda.events.google as google


class Command(BaseCommand):
    help = "Sync events with Google Calendar (two-way sync)"

    def handle(self, *args, **options):
        self.stdout.write("Starting Google Calendar sync...")

        try:
            google.sync_from_google()
            self.stdout.write(
                self.style.SUCCESS("✓ Google Calendar sync completed successfully")
            )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Sync failed: {e}"))
            raise
