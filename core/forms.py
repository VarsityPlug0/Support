from django import forms
from .models import SupportTicket, ProofOfPayment

class SupportTicketForm(forms.ModelForm):
    """Form for creating and editing support tickets"""
    class Meta:
        model = SupportTicket  # Use the SupportTicket model
        fields = ['title', 'description', 'priority']  # Fields to include in the form
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter ticket title'}),  # Bootstrap styling
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Describe your issue in detail'}),  # Textarea with styling
            'priority': forms.Select(attrs={'class': 'form-control'}),  # Dropdown with styling
        }

class ProofOfPaymentForm(forms.ModelForm):
    """Form for uploading proof of payment files"""
    class Meta:
        model = ProofOfPayment  # Use the ProofOfPayment model
        fields = ['email', 'reference_number', 'file']  # Fields to include in the form
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter your email'}),  # Email input with styling
            'reference_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Payment reference number (optional)'}),  # Text input with styling
            'file': forms.FileInput(attrs={'class': 'form-control'}),  # File input with styling
        } 