# app/vision/models.py

from django.db import models
from django.conf import settings

class WireframeUpload(models.Model):
    """Model to store user wireframe uploads and processing results"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wireframes'
    )
    image = models.ImageField(upload_to='wireframes/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    # Store detected elements from Vision API
    detected_elements = models.JSONField(null=True, blank=True)
    
    # Processing status
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    def __str__(self):
        return f"Wireframe by {self.user.email} at {self.uploaded_at}"
    
    class Meta:
        ordering = ['-uploaded_at']