from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from apps.notes.models import Note, NoteFolder


class NoteAdmin(SimpleHistoryAdmin):
    list_display = ("id", "title", "matter", "category")


class NoteFolderAdmin(SimpleHistoryAdmin):
    list_display = ("id", "name")


admin.site.register(Note, NoteAdmin)
admin.site.register(NoteFolder, NoteFolderAdmin)
