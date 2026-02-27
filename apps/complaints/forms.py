from django import forms
from .models import Complaint, ComplaintResponse


class ComplaintForm(forms.ModelForm):
    class Meta:
        model  = Complaint
        fields = ['category', 'priority', 'title', 'description', 'attachment']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Describe the issue in detail...'}),
            'title':       forms.TextInput(attrs={'placeholder': 'Brief title of the complaint'}),
        }


class ComplaintResponseForm(forms.ModelForm):
    class Meta:
        model  = ComplaintResponse
        fields = ['message', 'attachment']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Write your response...'}),
        }


class ComplaintStatusForm(forms.ModelForm):
    class Meta:
        model  = Complaint
        fields = ['status']

class OwnerComplaintForm(forms.ModelForm):
    class Meta:
        model  = Complaint
        fields = ['category', 'priority', 'title', 'description', 'attachment']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Describe the issue with tenant...'}),
            'title':       forms.TextInput(attrs={'placeholder': 'Brief title of the issue'}),
        }