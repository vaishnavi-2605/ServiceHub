from django import forms
from django.contrib.auth.forms import UserCreationForm
import re

from .models import CustomUser, ProviderProfile


def _is_valid_gmail(email_value):
    return bool(re.fullmatch(r"[A-Za-z0-9]+@gmail\.com", email_value or "", flags=re.IGNORECASE))


class SignupForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'username', 'email', 'mobile_no', 'address', 'role', 'password1', 'password2']

    username = forms.CharField(
        label='Username',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Choose username'})
    )

    first_name = forms.CharField(
        label='Full Name',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your name'})
    )

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'you@example.com'})
    )

    mobile_no = forms.CharField(
        label='Mobile Number',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '10-digit mobile',
            'maxlength': '10',
            'minlength': '10',
            'pattern': '[0-9]{10}',
            'inputmode': 'numeric',
        })
    )

    address = forms.CharField(
        label='Address',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Your address'})
    )

    role = forms.ChoiceField(
        choices=CustomUser.ROLE_CHOICES,
        widget=forms.RadioSelect,
        initial='user'
    )

    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Min 8 characters'}),
        label='Password'
    )

    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm password'}),
        label='Confirm Password'
    )

    def clean_mobile_no(self):
        mobile_no = (self.cleaned_data.get('mobile_no') or '').strip()
        if not mobile_no.isdigit() or len(mobile_no) != 10:
            raise forms.ValidationError('Mobile number must be exactly 10 digits.')
        return mobile_no

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip()
        if not _is_valid_gmail(email):
            raise forms.ValidationError('Please enter valid email.')
        return email.lower()


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'email', 'mobile_no', 'address']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'mobile_no': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip()
        if not _is_valid_gmail(email):
            raise forms.ValidationError('Please enter valid email.')
        return email.lower()


class ProviderProfileForm(forms.ModelForm):
    class Meta:
        model = ProviderProfile
        fields = ['phone', 'address', 'experience', 'bio', 'profile_image', 'certificate', 'aadhaar_card']
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'experience': forms.NumberInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'profile_image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'certificate': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'aadhaar_card': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }
