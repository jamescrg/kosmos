import django.db.models.deletion
from django.db import migrations, models


# Mapping from intake format to matter format
INTAKE_TO_MATTER_FORMAT = {
    "LLT - LL": "LLT-L",
    "LLT - T": "LLT-T",
}


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
    Intake = apps.get_model("intakes", "Intake")

    for intake in Intake.objects.exclude(practice_area__isnull=True):
        intake.practice_area_old = intake.practice_area.name
        intake.save(update_fields=["practice_area_old"])


class Migration(migrations.Migration):

    dependencies = [
        ("intakes", "0008_email_to_emailfield"),
        ("matters", "0023_practicearea_and_data_migration"),
    ]

    operations = [
        # Step 1: Rename existing practice_area field to practice_area_old
        migrations.RenameField(
            model_name="intake",
            old_name="practice_area",
            new_name="practice_area_old",
        ),
        # Step 2: Add new FK field for Intake
        migrations.AddField(
            model_name="intake",
            name="practice_area",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="intakes",
                to="matters.practicearea",
            ),
        ),
        # Step 3: Migrate Intake data
        migrations.RunPython(migrate_intake_practice_areas, reverse_migration),
        # Step 4: Remove old Intake field
        migrations.RemoveField(
            model_name="intake",
            name="practice_area_old",
        ),
    ]
