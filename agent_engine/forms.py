from django import forms
from django.contrib.auth.models import User
from .models import BusinessClient, KnowledgeDocument

class BusinessRegistrationForm(forms.ModelForm):
    username = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. luxestore'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'business@example.com'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': '••••••••'}), required=True)
    # Bug Fix #18: Added confirm_password field to prevent typos locking users out
    confirm_password = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': '••••••••'}),
        required=True
    )

    class Meta:
        model = BusinessClient
        fields = ['name', 'website_url', 'owner_whatsapp', 'bot_name', 'brand_color', 'welcome_message']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Luxe Interiors & Living'}),
            'website_url': forms.URLInput(attrs={'class': 'form-input', 'placeholder': 'https://yourbusiness.com'}),
            'owner_whatsapp': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '919876543210'}),
            'bot_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Aria - Sales Assistant'}),
            'brand_color': forms.TextInput(attrs={'class': 'form-input', 'type': 'color'}),
            'welcome_message': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm = cleaned_data.get('confirm_password')
        if password and confirm and password != confirm:
            self.add_error('confirm_password', 'Passwords do not match.')
        return cleaned_data

    def clean_username(self):
        # Bug Fix #19: Validate uniqueness inside the form to eliminate the manual
        # post-validation check in the view (which has a race-condition risk)
        from django.contrib.auth.models import User
        username = self.cleaned_data.get('username', '').strip()
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('This username is already taken. Please choose another.')
        return username

class BusinessSettingsForm(forms.ModelForm):
    class Meta:
        model = BusinessClient
        fields = ['name', 'website_url', 'owner_whatsapp', 'bot_name', 'brand_color', 'welcome_message', 'system_prompt']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input'}),
            'website_url': forms.URLInput(attrs={'class': 'form-input'}),
            'owner_whatsapp': forms.TextInput(attrs={'class': 'form-input'}),
            'bot_name': forms.TextInput(attrs={'class': 'form-input'}),
            'brand_color': forms.TextInput(attrs={'class': 'form-input', 'type': 'color'}),
            'welcome_message': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
            'system_prompt': forms.Textarea(attrs={'class': 'form-input', 'rows': 4, 'placeholder': 'Special rules for AI executive...'}),
        }

class ManualFAQForm(forms.ModelForm):
    class Meta:
        model = KnowledgeDocument
        fields = ['page_title', 'content_text']
        widgets = {
            'page_title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Return Policy / 2BHK Price Breakdown'}),
            'content_text': forms.Textarea(attrs={'class': 'form-input', 'rows': 4, 'placeholder': 'Enter complete information that bot should know...'}),
        }
