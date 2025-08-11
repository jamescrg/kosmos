from django import forms

from .models import Event


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = (
            "date",
            "matter",
            "party",
            "status",
            "description",
        )
        PARTIES = (
            ("Client", "Client"),
            ("Opposing", "Opposing"),
            ("All", "All"),
            ("Other", "Other"),
        )
        STATUSES = (
            ("Pending", "Pending"),
            ("Completed", "Completed"),
            ("Missed", "Missed"),
        )
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "description": forms.TextInput(
                attrs={
                    "autofocus": "autofocus",
                    "onfocus": "moveFocusToEnd(this)",
                    "class": "full-width",
                }
            ),
            "party": forms.Select(choices=PARTIES),
            "status": forms.Select(choices=STATUSES),
        }
