"""Watson search registration for global search models."""

from watson import search as watson

from apps.contacts.models import Contact
from apps.intakes.models import Intake
from apps.matters.models import Matter

# Register Matter model for search
watson.register(
    Matter,
    fields=("name", "work_status", "description"),
)

# Register Contact model for search
watson.register(
    Contact,
    fields=("name", "company", "email", "phone1", "phone2", "phone3", "notes"),
)

# Register Intake model for search
watson.register(
    Intake,
    fields=("name", "email", "phone"),
)

# Note: Note model is registered in apps.case.search_config
# Filtering for standalone notes (matter__isnull=True) happens in views
