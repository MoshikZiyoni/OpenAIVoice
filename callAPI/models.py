from django.db import models
from django.utils.timezone import localtime

class Call(models.Model):
    STATUS_CHOICES = [
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    phone_number = models.CharField(max_length=20)
    caller_id = models.CharField(max_length=20)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    call_sid = models.CharField(max_length=50, blank=True, null=True,unique=True)
    total_duration = models.FloatField(default=0)  # Total duration of the call in seconds
    conversation = models.JSONField(default=list)  # Store conversation as JSON
    direction = models.CharField(max_length=10, choices=(("in", "In"), ("out", "Out")))

    def add_conversation_turn(self, text, is_ai, duration=None):
        """
        Adds a conversation turn to the JSONField.
        """
        self.conversation.append({
            "text": text,
            "is_ai": is_ai,
        })
        if duration:
            self.total_duration += duration  # Update total duration
        self.save()

    def __str__(self):
        return f"Call to {self.phone_number} ({self.status})"
    def formatted_created_at(self):
        return localtime(self.created_at).strftime('%Y-%m-%d %H:%M')  # Format to 'YYYY-MM-DD HH:MM'

    def formatted_updated_at(self):
        return localtime(self.updated_at).strftime('%Y-%m-%d %H:%M')  # Format to 'YYYY-MM-DD HH:MM'

    def __str__(self):
        return f"Call created at: {self.formatted_created_at()}, updated at: {self.formatted_updated_at()}"
    
    # def __str__(self):
    #     return f"Call to {self.phone_number} ({self.status})"

# class ConversationTurn(models.Model):
#     call = models.ForeignKey(Call, on_delete=models.CASCADE, related_name='conversation')
#     text = models.TextField()
#     timestamp = models.DateTimeField(auto_now_add=True)
#     is_ai = models.BooleanField(default=True)
#     duration = models.FloatField(null=True, blank=True)  # Duration of the speech in seconds

#     def save(self, *args, **kwargs):
#         """
#         Override save method to update the total_duration of the related Call.
#         """
#         super().save(*args, **kwargs)  # Save the ConversationTurn
#         self.call.total_duration = sum(
#             turn.duration for turn in self.call.conversation.all() if turn.duration
#         )
#         self.call.save()

#     def __str__(self):
#         speaker = "AI" if self.is_ai else "Human"
#         return f"{speaker}: {self.text[:50]}..."