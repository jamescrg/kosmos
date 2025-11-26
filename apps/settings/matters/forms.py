from django import forms

from apps.matters.models import PracticeArea
from config.settings import CustomFormRendererCompact


class PracticeAreaForm(forms.ModelForm):
    class Meta:
        model = PracticeArea
        fields = ["name", "is_active"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.renderer = CustomFormRendererCompact()
