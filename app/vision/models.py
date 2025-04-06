# app/app/models.py
# (Update this path if your models are in a different location)

from django.db import models
from django.conf import settings  # ✅ Use settings.AUTH_USER_MODEL instead of importing User
from django.utils import timezone

class WireframeUpload(models.Model):
    """Model for storing wireframe uploads and processing results"""
    
    STATUS_CHOICES = (
        ('uploaded', 'Uploaded'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # ✅ This ensures compatibility with custom user models
        on_delete=models.CASCADE,
        related_name='wireframes'
    )
    title = models.CharField(max_length=255, default='Untitled Wireframe')
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='wireframes/')
    upload_date = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='uploaded')
    
    # Store Vision API detection results as JSON
    detected_elements = models.JSONField(blank=True, null=True)
    
    # Store Gemini generated code as JSON
    generated_code = models.JSONField(blank=True, null=True)
    
    class Meta:
        ordering = ['-upload_date']
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"
