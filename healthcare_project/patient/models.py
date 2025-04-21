# patient/models.py

from django.db import models
from accounts.models import User, PatientProfile, DoctorProfile

class MedicalRecord(models.Model):
    """Model for storing patient's medical records"""
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name='medical_records')
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name='doctor_records')
    diagnosis = models.TextField()
    symptoms = models.TextField()
    treatment = models.TextField()
    notes = models.TextField(blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Medical Record for {self.patient.user.get_full_name()} - {self.date_created.strftime('%Y-%m-%d')}"
    
    class Meta:
        ordering = ['-date_created']

class Appointment(models.Model):
    """Model for scheduling appointments between patients and doctors"""
    STATUS_CHOICES = (
        ('SCHEDULED', 'Scheduled'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
        ('NO_SHOW', 'No Show'),
    )
    
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name='appointments')
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SCHEDULED')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Appointment: {self.patient.user.get_full_name()} with Dr. {self.doctor.user.get_full_name()} on {self.appointment_date} at {self.appointment_time}"
    
    class Meta:
        ordering = ['appointment_date', 'appointment_time']
        unique_together = ('doctor', 'appointment_date', 'appointment_time')

class Prescription(models.Model):
    """Model for storing prescriptions"""
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name='prescriptions')
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name='prescribed')
    medical_record = models.ForeignKey(MedicalRecord, on_delete=models.CASCADE, related_name='prescriptions', null=True, blank=True)
    date_prescribed = models.DateField(auto_now_add=True)
    expiry_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Prescription for {self.patient.user.get_full_name()} by Dr. {self.doctor.user.get_full_name()} on {self.date_prescribed}"
    
    class Meta:
        ordering = ['-date_prescribed']

class Medicine(models.Model):
    """Model for storing medicine information"""
    name = models.CharField(max_length=100)
    description = models.TextField()
    manufacturer = models.CharField(max_length=100)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name

class PrescriptionItem(models.Model):
    """Model for storing medicine items in a prescription"""
    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE, related_name='items')
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE)
    dosage = models.CharField(max_length=100)  # e.g., "1 tablet twice a day"
    duration = models.CharField(max_length=100)  # e.g., "7 days"
    quantity = models.PositiveIntegerField()
    instructions = models.TextField()
    
    def __str__(self):
        return f"{self.medicine.name} for {self.prescription.patient.user.get_full_name()}"

class Bill(models.Model):
    """Model for storing billing information"""
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('PAID', 'Paid'),
        ('OVERDUE', 'Overdue'),
        ('CANCELLED', 'Cancelled'),
    )
    
    PAYMENT_METHOD_CHOICES = (
        ('CASH', 'Cash'),
        ('CREDIT_CARD', 'Credit Card'),
        ('DEBIT_CARD', 'Debit Card'),
        ('INSURANCE', 'Insurance'),
        ('BANK_TRANSFER', 'Bank Transfer'),
    )
    
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name='bills')
    appointment = models.OneToOneField(Appointment, on_delete=models.SET_NULL, null=True, blank=True, related_name='bill')
    prescription = models.OneToOneField(Prescription, on_delete=models.SET_NULL, null=True, blank=True, related_name='bill')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, null=True, blank=True)
    payment_date = models.DateTimeField(null=True, blank=True)
    due_date = models.DateField()
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Bill #{self.id} for {self.patient.user.get_full_name()} - {self.status}"
    
    def save(self, *args, **kwargs):
        self.total_amount = self.amount + self.tax - self.discount
        super().save(*args, **kwargs)
    
    class Meta:
        ordering = ['-created_at']

class Insurance(models.Model):
    """Model for storing insurance information"""
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name='insurances')
    provider_name = models.CharField(max_length=100)
    policy_number = models.CharField(max_length=50)
    coverage_start_date = models.DateField()
    coverage_end_date = models.DateField()
    coverage_details = models.TextField()
    contact_number = models.CharField(max_length=20)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.provider_name} - {self.policy_number} for {self.patient.user.get_full_name()}"
    
    class Meta:
        ordering = ['-coverage_start_date']

class InsuranceClaim(models.Model):
    """Model for processing insurance claims"""
    STATUS_CHOICES = (
        ('SUBMITTED', 'Submitted'),
        ('PROCESSING', 'Processing'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('COMPLETED', 'Completed'),
    )
    
    insurance = models.ForeignKey(Insurance, on_delete=models.CASCADE, related_name='claims')
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name='insurance_claims')
    claim_number = models.CharField(max_length=50)
    amount_claimed = models.DecimalField(max_digits=10, decimal_places=2)
    amount_approved = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SUBMITTED')
    submitted_date = models.DateField(auto_now_add=True)
    processed_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"Claim #{self.claim_number} - {self.insurance.provider_name} for {self.bill.patient.user.get_full_name()}"
    
    class Meta:
        ordering = ['-submitted_date']