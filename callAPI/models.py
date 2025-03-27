from django.db import models

class Call(models.Model):
    STATUS_CHOICES = [
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    phone_number = models.CharField(max_length=20)
    caller_id = models.CharField(max_length=20)
    prompt = models.TextField(default="You are a helpful assistant. Listen carefully and respond appropriately.")
    voice = models.CharField(max_length=50, default='alloy')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    call_sid = models.CharField(max_length=50, blank=True, null=True)
    
    def __str__(self):
        return f"Call to {self.phone_number} ({self.status})"

class ConversationTurn(models.Model):
    call = models.ForeignKey(Call, on_delete=models.CASCADE, related_name='conversation')
    text = models.TextField()
    is_ai = models.BooleanField(default=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['timestamp']
    
    def __str__(self):
        speaker = "AI" if self.is_ai else "Human"
        return f"{speaker}: {self.text[:50]}..."
    

class MediaFile(models.Model):
    name = models.CharField(max_length=255)
    file = models.FileField(upload_to='media_files/')  # This will save files in MEDIA_ROOT/media_files/

    def __str__(self):
        return self.name