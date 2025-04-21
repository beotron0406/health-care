# doctor/models.py

from django.db import models
from accounts.models import User, DoctorProfile, PatientProfile, NurseProfile
from patient.models import MedicalRecord, Appointment, Prescription

class DoctorSchedule(models.Model):
    """Model for managing doctor's schedule and availability"""
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name='schedules')
    day_of_week = models.CharField(max_length=10)  # Monday, Tuesday, etc.
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_available = models.BooleanField(default=True)
    
    def __str__(self):
        return f"Dr. {self.doctor.user.get_full_name()} - {self.day_of_week} ({self.start_time} - {self.end_time})"
    
    class Meta:
        unique_together = ('doctor', 'day_of_week', 'start_time')
        ordering = ['day_of_week', 'start_time']

class DoctorLeave(models.Model):
    """Model for managing doctor's leave or unavailability"""
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    )
    
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name='leaves')
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_leaves')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Dr. {self.doctor.user.get_full_name()} - {self.start_date} to {self.end_date} ({self.get_status_display()})"
    
    class Meta:
        ordering = ['-start_date']

class Treatment(models.Model):
    """Model for storing treatments prescribed by doctors"""
    medical_record = models.OneToOneField(MedicalRecord, on_delete=models.CASCADE, related_name='treatment')
    treatment_plan = models.TextField()
    follow_up_date = models.DateField(null=True, blank=True)
    follow_up_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Treatment for {self.medical_record.patient.user.get_full_name()} - {self.medical_record.date_created.strftime('%Y-%m-%d')}"

class PatientNote(models.Model):
    """Model for storing doctor's private notes about patients"""
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name='patient_notes')
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name='doctor_notes')
    note = models.TextField()
    is_private = models.BooleanField(default=True)  # If true, only the doctor can see it
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Note for {self.patient.user.get_full_name()} by Dr. {self.doctor.user.get_full_name()}"
    
    class Meta:
        ordering = ['-created_at']

class Referral(models.Model):
    """Model for managing patient referrals to specialists or other doctors"""
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('ACCEPTED', 'Accepted'),
        ('COMPLETED', 'Completed'),
        ('DECLINED', 'Declined'),
    )
    
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name='referrals')
    referring_doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name='outgoing_referrals')
    referred_to_doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name='incoming_referrals')
    medical_record = models.ForeignKey(MedicalRecord, on_delete=models.CASCADE, related_name='referrals', null=True, blank=True)
    reason = models.TextField()
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    referral_date = models.DateField(auto_now_add=True)
    completion_date = models.DateField(null=True, blank=True)
    
    def __str__(self):
        return f"Referral for {self.patient.user.get_full_name()} from Dr. {self.referring_doctor.user.get_full_name()} to Dr. {self.referred_to_doctor.user.get_full_name()}"
    
    class Meta:
        ordering = ['-referral_date']

class Task(models.Model):
    """Model for assigning tasks to nurses or other staff"""
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    )
    
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name='assigned_tasks')
    assigned_to = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks')
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name='tasks', null=True, blank=True)
    title = models.CharField(max_length=100)
    description = models.TextField()
    priority = models.IntegerField(default=0)  # 0 = Low, 1 = Medium, 2 = High
    due_date = models.DateTimeField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.title} - Assigned to {self.assigned_to.get_full_name()} by Dr. {self.doctor.user.get_full_name()}"
    
    class Meta:
        ordering = ['priority', 'due_date']

class NurseAssignment(models.Model):
    """Model for assigning nurses to doctors or departments"""
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name='assigned_nurses')
    nurse = models.ForeignKey(NurseProfile, on_delete=models.CASCADE, related_name='assigned_doctors')
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Nurse {self.nurse.user.get_full_name()} assigned to Dr. {self.doctor.user.get_full_name()}"
    
    class Meta:
        unique_together = ('doctor', 'nurse', 'start_date')
        ordering = ['-start_date']

class DoctorAvailableTimeSlot(models.Model):
    """Model for managing specific time slots availability for doctors"""
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name='available_slots')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Dr. {self.doctor.user.get_full_name()} - {self.date} ({self.start_time} - {self.end_time})"
    
    class Meta:
        unique_together = ('doctor', 'date', 'start_time')
        ordering = ['date', 'start_time']