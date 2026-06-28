from django import forms

from apps.invoicing.requests.models import PaymentRequest
from config.settings import CustomFormRendererCompact


class PaymentRequestForm(forms.ModelForm):
    class Meta:
        model = PaymentRequest
        fields = ["matter", "recipient_email"]
        widgets = {
            "matter": forms.Select(),
            "recipient_email": forms.EmailInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.renderer = CustomFormRendererCompact()
