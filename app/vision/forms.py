# app/vision/forms.py
from django import forms
from .models import WireframeUpload

class ImageUploadForm(forms.ModelForm):
    class Meta:
        model = WireframeUpload
        fields = ['image']
        widgets = {
            'image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'})
        }