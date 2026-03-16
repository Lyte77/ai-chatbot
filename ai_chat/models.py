from django.db import models

# Create your models here.

class Message(models.Model):
    """
    Stores a single exchange — one user message and one AI response.
    """
    user_message = models.TextField()
    ai_response = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)  # set automatically on save

    class Meta:
        ordering = ['created_at']  # oldest first — natural chat order

    def __str__(self):
        return f"Message at {self.created_at:%Y-%m-%d %H:%M}"