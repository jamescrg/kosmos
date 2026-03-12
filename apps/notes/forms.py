from django import forms

from config.settings import CustomFormRendererCompact

from .models import Note, NoteFolder


class NoteForm(forms.ModelForm):
    default_renderer = CustomFormRendererCompact

    class Meta:
        model = Note
        fields = ["category", "topic", "title"]
        widgets = {
            "title": forms.TextInput(attrs={"autofocus": True, "class": "span2"}),
            "category": forms.Select(),
            "topic": forms.TextInput(attrs={"class": "span2"}),
        }


class NoteFolderForm(forms.ModelForm):
    class Meta:
        model = NoteFolder
        fields = ["name"]

        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Folder name",
                    "autofocus": True,
                    "onfocus": "moveFocusToEnd(this)",
                }
            ),
        }

        labels = {
            "name": "Folder Name",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["name"].required = True
