from django.db import migrations, models


class Migration(migrations.Migration):
    """Split the old `location` choice field into `event_type` (the
    Zoom/Virtual/Phone/In-person dropdown) and a new free-text `location`.

    The existing column held the meeting type, so rename it to `event_type`
    to carry that data over, then add a fresh, empty free-text `location`.
    """

    dependencies = [
        ("calendar", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(
            model_name="event",
            old_name="location",
            new_name="event_type",
        ),
        migrations.RenameField(
            model_name="historicalevent",
            old_name="location",
            new_name="event_type",
        ),
        migrations.AddField(
            model_name="event",
            name="location",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="historicalevent",
            name="location",
            field=models.TextField(blank=True, null=True),
        ),
    ]
