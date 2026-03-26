from django.db import migrations, models


def convert_importance(apps, schema_editor):
    """Invert and compress importance from 1-10 scale to 1-5 scale.

    Mapping: 1-2→5, 3-4→4, 5-6→3, 7-8→2, 9-10→1
    """
    Note = apps.get_model("notes", "Note")
    mapping = {1: 5, 2: 5, 3: 4, 4: 4, 5: 3, 6: 3, 7: 2, 8: 2, 9: 1, 10: 1}
    for old_val, new_val in mapping.items():
        Note.objects.filter(importance=old_val).update(importance=new_val)


def reverse_importance(apps, schema_editor):
    """Reverse: expand importance from 1-5 back to 1-10 (using midpoint)."""
    Note = apps.get_model("notes", "Note")
    mapping = {5: 1, 4: 3, 3: 5, 2: 7, 1: 9}
    for old_val, new_val in mapping.items():
        Note.objects.filter(importance=old_val).update(importance=new_val)


class Migration(migrations.Migration):

    dependencies = [
        ("notes", "0012_create_research_topic_folders"),
    ]

    operations = [
        migrations.RunPython(convert_importance, reverse_importance),
        migrations.AlterField(
            model_name="note",
            name="importance",
            field=models.PositiveIntegerField(default=3),
        ),
    ]
