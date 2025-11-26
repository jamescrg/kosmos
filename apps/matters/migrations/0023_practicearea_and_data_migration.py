import django.db.models.deletion
from django.db import migrations, models


# Canonical practice areas (Matter format)
PRACTICE_AREAS = [
    "General",
    "Interpleader",
    "Construction",
    "Boundary",
    "LLT-L",
    "LLT-T",
    "QT",
    "Title",
    "HOA",
    "Fraud",
]

# Mapping from intake format to matter format
INTAKE_TO_MATTER_FORMAT = {
    "LLT - LL": "LLT-L",
    "LLT - T": "LLT-T",
}


def populate_practice_areas(apps, schema_editor):
    """Create practice area records from the canonical list."""
    PracticeArea = apps.get_model("matters", "PracticeArea")
    for name in PRACTICE_AREAS:
        PracticeArea.objects.get_or_create(name=name, defaults={"is_active": True})


def migrate_matter_practice_areas(apps, schema_editor):
    """Migrate matter practice_area CharField values to FK references."""
    Matter = apps.get_model("matters", "Matter")
    PracticeArea = apps.get_model("matters", "PracticeArea")

    for matter in Matter.objects.exclude(practice_area_old__isnull=True).exclude(
        practice_area_old=""
    ):
        practice_area_name = matter.practice_area_old
        try:
            pa = PracticeArea.objects.get(name=practice_area_name)
            matter.practice_area = pa
            matter.save(update_fields=["practice_area"])
        except PracticeArea.DoesNotExist:
            # Create the practice area if it doesn't exist
            pa = PracticeArea.objects.create(name=practice_area_name, is_active=True)
            matter.practice_area = pa
            matter.save(update_fields=["practice_area"])


def migrate_intake_practice_areas(apps, schema_editor):
    """Migrate intake practice_area CharField values to FK references."""
    Intake = apps.get_model("intakes", "Intake")
    PracticeArea = apps.get_model("matters", "PracticeArea")

    for intake in Intake.objects.exclude(practice_area_old__isnull=True).exclude(
        practice_area_old=""
    ):
        practice_area_name = intake.practice_area_old
        # Map intake format to matter format
        practice_area_name = INTAKE_TO_MATTER_FORMAT.get(
            practice_area_name, practice_area_name
        )
        try:
            pa = PracticeArea.objects.get(name=practice_area_name)
            intake.practice_area = pa
            intake.save(update_fields=["practice_area"])
        except PracticeArea.DoesNotExist:
            # Create the practice area if it doesn't exist
            pa = PracticeArea.objects.create(name=practice_area_name, is_active=True)
            intake.practice_area = pa
            intake.save(update_fields=["practice_area"])


def reverse_migration(apps, schema_editor):
    """Reverse migration - copy FK names back to char fields."""
    Matter = apps.get_model("matters", "Matter")
    Intake = apps.get_model("intakes", "Intake")

    for matter in Matter.objects.exclude(practice_area__isnull=True):
        matter.practice_area_old = matter.practice_area.name
        matter.save(update_fields=["practice_area_old"])

    for intake in Intake.objects.exclude(practice_area__isnull=True):
        intake.practice_area_old = intake.practice_area.name
        intake.save(update_fields=["practice_area_old"])


class Migration(migrations.Migration):

    dependencies = [
        ("matters", "0022_cascade_delete_group_role"),
        ("intakes", "0008_email_to_emailfield"),
    ]

    operations = [
        # Step 1: Create PracticeArea model
        migrations.CreateModel(
            name="PracticeArea",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=50)),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={
                "db_table": "app_practice_area",
                "ordering": ["name"],
            },
        ),
        # Step 2: Populate practice areas
        migrations.RunPython(populate_practice_areas, migrations.RunPython.noop),
        # Step 3: Rename existing practice_area fields to practice_area_old
        migrations.RenameField(
            model_name="matter",
            old_name="practice_area",
            new_name="practice_area_old",
        ),
        # Step 4: Add new FK field for Matter
        migrations.AddField(
            model_name="matter",
            name="practice_area",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="matters",
                to="matters.practicearea",
            ),
        ),
        # Step 5: Migrate Matter data
        migrations.RunPython(migrate_matter_practice_areas, reverse_migration),
        # Step 6: Remove old Matter field
        migrations.RemoveField(
            model_name="matter",
            name="practice_area_old",
        ),
    ]
