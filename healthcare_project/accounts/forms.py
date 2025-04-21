# accounts/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, PatientProfile, DoctorProfile, NurseProfile, PharmacistProfile, LabTechnicianProfile

class UserRegistrationForm(UserCreationForm):
    """Form for user registration with extended fields."""
    
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    user_type = forms.ChoiceField(choices=User.USER_TYPE_CHOICES)
    phone_number = forms.CharField(required=False)
    address = forms.CharField(widget=forms.Textarea, required=False)
    date_of_birth = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    profile_picture = forms.ImageField(required=False)
    
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'user_type', 'phone_number', 
                  'address', 'date_of_birth', 'profile_picture', 'password1', 'password2']

class PatientProfileForm(forms.ModelForm):
    """Form for patient-specific profile information."""
    
    class Meta:
        model = PatientProfile
        fields = ['blood_group', 'emergency_contact_name', 'emergency_contact_number', 
                  'allergies', 'chronic_diseases', 'insurance_provider', 'insurance_id']

class DoctorProfileForm(forms.ModelForm):
    """Form for doctor-specific profile information."""
    
    class Meta:
        model = DoctorProfile
        fields = ['specialization', 'qualification', 'license_number', 
                  'years_of_experience', 'consultation_fee', 'available_days', 'available_times']
        widgets = {
            'available_days': forms.TextInput(attrs={'placeholder': 'Monday, Tuesday, Wednesday...'}),
            'available_times': forms.TextInput(attrs={'placeholder': '9:00-12:00, 14:00-17:00...'}),
        }

class NurseProfileForm(forms.ModelForm):
    """Form for nurse-specific profile information."""
    
    class Meta:
        model = NurseProfile
        fields = ['qualification', 'license_number', 'years_of_experience', 'department']

class PharmacistProfileForm(forms.ModelForm):
    """Form for pharmacist-specific profile information."""
    
    class Meta:
        model = PharmacistProfile
        fields = ['qualification', 'license_number', 'years_of_experience']

class LabTechnicianProfileForm(forms.ModelForm):
    """Form for lab technician-specific profile information."""
    
    class Meta:
        model = LabTechnicianProfile
        fields = ['qualification', 'specialization', 'license_number', 'years_of_experience']

class CustomAuthenticationForm(AuthenticationForm):
    """Custom authentication form with email instead of username."""
    
    username = forms.EmailField(label='Email')