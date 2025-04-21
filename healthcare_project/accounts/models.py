# accounts/models.py

from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _

class UserManager(BaseUserManager):
    """Define a model manager for User model with no username field."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError('The email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular User with the given email and password."""
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('user_type', 'ADMIN')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)

class User(AbstractUser):
    """Custom User model for healthcare system with email as the unique identifier."""
    
    USER_TYPE_CHOICES = (
        ('PATIENT', 'Patient'),
        ('DOCTOR', 'Doctor'),
        ('NURSE', 'Nurse'),
        ('ADMIN', 'Administrator'),
        ('PHARMACIST', 'Pharmacist'),
        ('INSURANCE', 'Insurance Provider'),
        ('LAB_TECH', 'Laboratory Technician'),
    )
    
    username = None
    email = models.EmailField(_('email address'), unique=True)
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES)
    phone_number = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'user_type']

    objects = UserManager()

    def __str__(self):
        return f"{self.get_full_name()} ({self.get_user_type_display()})"
    
    def get_role_specific_profile(self):
        """Return the role-specific profile for this user."""
        if self.user_type == 'PATIENT':
            return hasattr(self, 'patient_profile') and self.patient_profile or None
        elif self.user_type == 'DOCTOR':
            return hasattr(self, 'doctor_profile') and self.doctor_profile or None
        elif self.user_type == 'NURSE':
            return hasattr(self, 'nurse_profile') and self.nurse_profile or None
        elif self.user_type == 'PHARMACIST':
            return hasattr(self, 'pharmacist_profile') and self.pharmacist_profile or None
        elif self.user_type == 'LAB_TECH':
            return hasattr(self, 'lab_tech_profile') and self.lab_tech_profile or None
        return None

class PatientProfile(models.Model):
    """Extended profile for Patient users."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='patient_profile')
    blood_group = models.CharField(max_length=5, blank=True)
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_number = models.CharField(max_length=15, blank=True)
    allergies = models.TextField(blank=True)
    chronic_diseases = models.TextField(blank=True)
    insurance_provider = models.CharField(max_length=100, blank=True)
    insurance_id = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return f"Patient: {self.user.get_full_name()}"

class DoctorProfile(models.Model):
    """Extended profile for Doctor users."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='doctor_profile')
    specialization = models.CharField(max_length=100)
    qualification = models.TextField()
    license_number = models.CharField(max_length=50)
    years_of_experience = models.PositiveIntegerField(default=0)
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    available_days = models.CharField(max_length=100, blank=True)  # CSV of days
    available_times = models.CharField(max_length=100, blank=True)  # CSV of times

    def __str__(self):
        return f"Dr. {self.user.get_full_name()} ({self.specialization})"

class NurseProfile(models.Model):
    """Extended profile for Nurse users."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='nurse_profile')
    qualification = models.TextField()
    license_number = models.CharField(max_length=50)
    years_of_experience = models.PositiveIntegerField(default=0)
    department = models.CharField(max_length=100)

    def __str__(self):
        return f"Nurse: {self.user.get_full_name()}"

class PharmacistProfile(models.Model):
    """Extended profile for Pharmacist users."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='pharmacist_profile')
    qualification = models.TextField()
    license_number = models.CharField(max_length=50)
    years_of_experience = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Pharmacist: {self.user.get_full_name()}"

class LabTechnicianProfile(models.Model):
    """Extended profile for Laboratory Technician users."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='lab_tech_profile')
    qualification = models.TextField()
    specialization = models.CharField(max_length=100)
    license_number = models.CharField(max_length=50)
    years_of_experience = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Lab Technician: {self.user.get_full_name()}"