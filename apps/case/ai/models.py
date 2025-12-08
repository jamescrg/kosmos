from django.db import models

from apps.accounts.models import CustomUser
from apps.matters.models import Matter


class Conversation(models.Model):
    """A chat conversation within a matter context."""

    matter = models.ForeignKey(
        Matter, on_delete=models.CASCADE, related_name="ai_conversations"
    )
    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="ai_conversations"
    )
    title = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        db_table = "matters_conversation"  # Keep same table name

    def __str__(self):
        return f"{self.matter.name} - {self.title or 'Untitled'}"


class Message(models.Model):
    """Individual message in a conversation."""

    ROLE_CHOICES = [
        ("user", "User"),
        ("assistant", "Assistant"),
    ]

    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name="messages"
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    # Track token usage for monitoring
    input_tokens = models.IntegerField(null=True, blank=True)
    output_tokens = models.IntegerField(null=True, blank=True)

    class Meta:
        ordering = ["created_at"]
        db_table = "matters_message"  # Keep same table name

    def __str__(self):
        return f"{self.role}: {self.content[:50]}..."
