# doctor/forms.py

from django import forms
from django.utils import timezone
from .models import (
    DoctorSchedule, DoctorLeave, Treatment, 
    PatientNote, Referral, Task, NurseAssignment,
    DoctorAvailableTimeSlot
)
from accounts.models import User, PatientProfile, DoctorProfile, NurseProfile
from patient.models import MedicalRecord, Appointment, Prescription, PrescriptionItem, Medicine

class DoctorScheduleForm(forms.ModelForm):
    """Form for creating/updating doctor schedules"""
    DAY_CHOICES = [
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
        ('Saturday', 'Saturday'),
        ('Sunday', 'Sunday'),
    ]
    
    day_of_week = forms.ChoiceField(
        choices=DAY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    start_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'})
    )
    end_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'})
    )
    is_available = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    class Meta:
        model = DoctorSchedule
        fields = ['day_of_week', 'start_time', 'end_time', 'is_available']
    
    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        
        if start_time and end_time and start_time >= end_time:
            raise forms.ValidationError("End time must be later than start time.")
        
        return cleaned_data

class DoctorLeaveForm(forms.ModelForm):
    """Form for requesting/managing doctor leaves"""
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    reason = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
    
    class Meta:
        model = DoctorLeave
        fields = ['start_date', 'end_date', 'reason']
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and start_date < timezone.now().date():
            raise forms.ValidationError("Start date cannot be in the past.")
        
        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError("End date must be later than or equal to start date.")
        
        return cleaned_data

class MedicalRecordForm(forms.ModelForm):
    """Form for creating/updating medical records"""
    diagnosis = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
    symptoms = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
    treatment = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
    notes = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        required=False
    )
    
    class Meta:
        model = MedicalRecord
        fields = ['diagnosis', 'symptoms', 'treatment', 'notes']

class TreatmentForm(forms.ModelForm):
    """Form for creating/updating treatment plans"""
    treatment_plan = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4})
    )
    follow_up_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        required=False
    )
    follow_up_notes = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        required=False
    )
    
    class Meta:
        model = Treatment
        fields = ['treatment_plan', 'follow_up_date', 'follow_up_notes']
    
    def clean_follow_up_date(self):
        follow_up_date = self.cleaned_data.get('follow_up_date')
        if follow_up_date and follow_up_date < timezone.now().date():
            raise forms.ValidationError("Follow-up date cannot be in the past.")
        return follow_up_date

class PatientNoteForm(forms.ModelForm):
    """Form for creating/updating patient notes"""
    note = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4})
    )
    is_private = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    class Meta:
        model = PatientNote
        fields = ['note', 'is_private']

class ReferralForm(forms.ModelForm):
    """Form for creating patient referrals"""
    referred_to_doctor = forms.ModelChoiceField(
        queryset=DoctorProfile.objects.all(),
        empty_label="Select Doctor",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    reason = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
    notes = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        required=False
    )
    
    class Meta:
        model = Referral
        fields = ['referred_to_doctor', 'reason', 'notes']
    
    def __init__(self, *args, **kwargs):
        referring_doctor = kwargs.pop('referring_doctor', None)
        super().__init__(*args, **kwargs)
        
        if referring_doctor:
            # Exclude the referring doctor from the list of doctors to refer to
            self.fields['referred_to_doctor'].queryset = DoctorProfile.objects.exclude(id=referring_doctor.id)

class TaskForm(forms.ModelForm):
    """Form for assigning tasks to staff"""
    assigned_to = forms.ModelChoiceField(
        queryset=User.objects.filter(user_type__in=['NURSE', 'LAB_TECH']),
        empty_label="Select Staff Member",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    patient = forms.ModelChoiceField(
        queryset=PatientProfile.objects.all(),
        empty_label="Select Patient (Optional)",
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    title = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    description = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
    priority = forms.ChoiceField(
        choices=[(0, 'Low'), (1, 'Medium'), (2, 'High')],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    due_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'})
    )
    
    class Meta:
        model = Task
        fields = ['assigned_to', 'patient', 'title', 'description', 'priority', 'due_date']
    
    def clean_due_date(self):
        due_date = self.cleaned_data.get('due_date')
        if due_date and due_date < timezone.now():
            raise forms.ValidationError("Due date cannot be in the past.")
        return due_date

class NurseAssignmentForm(forms.ModelForm):
    """Form for assigning nurses to doctors"""
    nurse = forms.ModelChoiceField(
        queryset=NurseProfile.objects.all(),
        empty_label="Select Nurse",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        required=False
    )
    is_active = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    class Meta:
        model = NurseAssignment
        fields = ['nurse', 'start_date', 'end_date', 'is_active']
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and start_date < timezone.now().date():
            raise forms.ValidationError("Start date cannot be in the past.")
        
        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError("End date must be later than or equal to start date.")
        
        return cleaned_data

class AppointmentUpdateForm(forms.ModelForm):
    """Form for updating appointments"""
    STATUS_CHOICES = [
        ('SCHEDULED', 'Scheduled'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
        ('NO_SHOW', 'No Show'),
    ]
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    notes = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        required=False
    )
    
    class Meta:
        model = Appointment
        fields = ['status', 'notes']

class PrescriptionForm(forms.ModelForm):
    """Form for creating/updating prescriptions"""
    notes = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        required=False
    )
    expiry_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        required=False
    )
    is_active = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    class Meta:
        model = Prescription
        fields = ['notes', 'expiry_date', 'is_active']
    
    def clean_expiry_date(self):
        expiry_date = self.cleaned_data.get('expiry_date')
        if expiry_date and expiry_date < timezone.now().date():
            raise forms.ValidationError("Expiry date cannot be in the past.")
        return expiry_date

class PrescriptionItemForm(forms.ModelForm):
    """Form for adding medicine items to a prescription"""
    medicine = forms.ModelChoiceField(
        queryset=Medicine.objects.all(),
        empty_label="Select Medicine",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    dosage = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text="E.g., 1 tablet twice a day"
    )
    duration = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text="E.g., 7 days"
    )
    quantity = forms.IntegerField(
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        min_value=1
    )
    instructions = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        help_text="Special instructions for taking this medicine"
    )
    
    class Meta:
        model = PrescriptionItem
        fields = ['medicine', 'dosage', 'duration', 'quantity', 'instructions']
    
    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        medicine = self.cleaned_data.get('medicine')
        
        if medicine and quantity > medicine.stock_quantity:
            raise forms.ValidationError(f"Not enough stock. Available: {medicine.stock_quantity}")
        
        return quantity

class DoctorAvailableTimeSlotForm(forms.ModelForm):
    """Form for setting specific available time slots"""
    date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    start_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'})
    )
    end_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'})
    )
    is_available = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    class Meta:
        model = DoctorAvailableTimeSlot
        fields = ['date', 'start_time', 'end_time', 'is_available']
    
    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get('date')
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        
        if date and date < timezone.now().date():
            raise forms.ValidationError("Date cannot be in the past.")
        
        if start_time and end_time and start_time >= end_time:
            raise forms.ValidationError("End time must be later than start time.")
        
        return cleaned_data