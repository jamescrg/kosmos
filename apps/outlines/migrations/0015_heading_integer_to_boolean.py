"""
Convert heading field from PositiveIntegerField (2-5) to BooleanField.
Any existing heading value (2-5) becomes True, NULL becomes False.
"""

from django.db import migrations, models


def convert_heading_to_boolean(apps, schema_editor):
    """Convert integer heading values to boolean."""
    OutlineItem = apps.get_model("outlines", "OutlineItem")
    # Any non-null heading value becomes True
    OutlineItem.objects.filter(heading__isnull=False).update(heading=1)
    # Null values become False (0)
    OutlineItem.objects.filter(heading__isnull=True).update(heading=0)


def reverse_heading_to_integer(apps, schema_editor):
    """Reverse: convert boolean back to integer (True -> 2, False -> None)."""
    OutlineItem = apps.get_model("outlines", "OutlineItem")
    # True (1) becomes heading level 2
    OutlineItem.objects.filter(heading=1).update(heading=2)
    # False (0) becomes NULL
    OutlineItem.objects.filter(heading=0).update(heading=None)


class Migration(migrations.Migration):

    dependencies = [
        ("outlines", "0014_add_quote_field"),
    ]

    operations = [
        # First convert the data while still an integer field
        migrations.RunPython(
            convert_heading_to_boolean,
            reverse_heading_to_integer,
        ),
        # Then alter the field type
        migrations.AlterField(
            model_name="outlineitem",
            name="heading",
            field=models.BooleanField(default=False),
        ),
    ]
