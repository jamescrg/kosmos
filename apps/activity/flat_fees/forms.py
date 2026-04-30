from django import forms

from apps.accounts.access import filter_matters_for_user
from apps.matters.models import Matter
from config.settings import CustomFormRendererCompact

from .models import FlatFeeEntry


class FlatFeeEntryForm(forms.ModelForm):
    class Meta:
        model = FlatFeeEntry

        fields = (
            "matter",
            "date",
            "description",
            "amount",
            "comp",
            "entered",
        )

        COMP_CHOICES = (
            (False, "No"),
            (True, "Yes"),
        )

        ENTERED_CHOICES = (
            (False, "No"),
            (True, "Yes"),
        )

        widgets = {
            "matter": forms.Select(
                attrs={"onchange": "updateAmount()", "tabindex": "1"}
            ),
            "date": forms.DateInput(attrs={"type": "date", "tabindex": "4"}),
            "description": forms.Textarea(
                attrs={
                    "onfocus": "moveFocusToEnd(this)",
                    "rows": "3",
                    "class": "span2",
                    "tabindex": "2",
                    "autofocus": True,
                }
            ),
            "comp": forms.Select(choices=COMP_CHOICES),
            "entered": forms.Select(choices=ENTERED_CHOICES),
        }

        labels = {"amount": "Amount"}

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        self.renderer = CustomFormRendererCompact()
        self.fields["amount"].widget.attrs["tabindex"] = "3"
        queryset = Matter.objects.filter(billing_type="FLAT_FEE")
        if user:
            queryset = filter_matters_for_user(queryset, user)
        self.fields["matter"].queryset = queryset

    def clean_matter(self):
        matter = self.cleaned_data.get("matter")
        if matter and matter.billing_type != "FLAT_FEE":
            raise forms.ValidationError(
                "Flat-fee entries can only be logged on flat-fee matters."
            )
        return matter
