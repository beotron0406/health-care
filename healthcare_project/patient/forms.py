# patient/forms.py

from django import forms
from django.utils import timezone
from .models import (
    Appointment, MedicalRecord, Prescription, 
    PrescriptionItem, Bill, Insurance, InsuranceClaim
)
from accounts.models import DoctorProfile

class AppointmentForm(forms.ModelForm):
    """Form for booking appointments"""
    doctor = forms.ModelChoiceField(
        queryset=DoctorProfile.objects.all(),
        empty_label="Select Doctor",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    appointment_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        help_text="Select a date for your appointment"
    )
    appointment_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        help_text="Select a time for your appointment"
    )
    reason = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        help_text="Please describe the reason for your appointment"
    )
    
    class Meta:
        model = Appointment
        fields = ['doctor', 'appointment_date', 'appointment_time', 'reason']
        
    def clean_appointment_date(self):
        date = self.cleaned_data.get('appointment_date')
        if date < timezone.now().date():
            raise forms.ValidationError("Appointment date cannot be in the past.")
        return date
    
    def clean(self):
        cleaned_data = super().clean()
        doctor = cleaned_data.get('doctor')
        date = cleaned_data.get('appointment_date')
        time = cleaned_data.get('appointment_time')
        
        if doctor and date and time:
            # Check if doctor is available on this day
            day_name = date.strftime('%A')
            if doctor.available_days and day_name not in doctor.available_days:
                raise forms.ValidationError(f"Doctor is not available on {day_name}s.")
            
            # Check if the slot is already booked
            if Appointment.objects.filter(
                doctor=doctor,
                appointment_date=date,
                appointment_time=time,
                status='SCHEDULED'
            ).exists():
                raise forms.ValidationError("This time slot is already booked. Please select another time.")
        
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

class InsuranceForm(forms.ModelForm):
    """Form for adding/updating insurance information"""
    provider_name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    policy_number = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    coverage_start_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    coverage_end_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    coverage_details = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
    contact_number = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    is_active = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    class Meta:
        model = Insurance
        fields = ['provider_name', 'policy_number', 'coverage_start_date', 
                 'coverage_end_date', 'coverage_details', 'contact_number', 'is_active']
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('coverage_start_date')
        end_date = cleaned_data.get('coverage_end_date')
        
        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError("Coverage end date cannot be before start date.")
        
        return cleaned_data

class BillPaymentForm(forms.ModelForm):
    """Form for processing bill payments"""
    payment_method = forms.ChoiceField(
        choices=Bill.PAYMENT_METHOD_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    class Meta:
        model = Bill
        fields = ['payment_method']

class InsuranceClaimForm(forms.ModelForm):
    """Form for submitting insurance claims"""
    insurance = forms.ModelChoiceField(
        queryset=Insurance.objects.none(),  # Will be set in the view
        empty_label="Select Insurance Provider",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    amount_claimed = forms.DecimalField(
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        min_value=0.01
    )
    notes = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        required=False
    )
    
    class Meta:
        model = InsuranceClaim
        fields = ['insurance', 'amount_claimed', 'notes']
    
    def __init__(self, *args, **kwargs):
        patient = kwargs.pop('patient', None)
        super().__init__(*args, **kwargs)
        
        if patient:
            # Only show active insurance policies for the patient
            self.fields['insurance'].queryset = Insurance.objects.filter(
                patient=patient,
                is_active=True,
                coverage_end_date__gte=timezone.now().date()
            )
    
    def clean_amount_claimed(self):
        amount = self.cleaned_data.get('amount_claimed')
        bill = self.instance.bill if hasattr(self.instance, 'bill') else None
        
        if bill and amount > bill.total_amount:
            raise forms.ValidationError("Amount claimed cannot exceed the bill amount.")
        
        return amount

class PrescriptionItemForm(forms.ModelForm):
    """Form for adding medicine items to a prescription"""
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
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['medicine'].widget.attrs.update({'class': 'form-select'})
    
    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        medicine = self.cleaned_data.get('medicine')
        
        if medicine and quantity > medicine.stock_quantity:
            raise forms.ValidationError(f"Not enough stock. Available: {medicine.stock_quantity}")
        
        return quantity