# accounts/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.db import transaction

from .forms import (
    UserRegistrationForm, CustomAuthenticationForm,
    PatientProfileForm, DoctorProfileForm, NurseProfileForm,
    PharmacistProfileForm, LabTechnicianProfileForm
)
from .models import User, PatientProfile, DoctorProfile, NurseProfile, PharmacistProfile, LabTechnicianProfile

def home(request):
    """Home page view."""
    return render(request, 'accounts/home.html')

def register_view(request):
    """User registration view."""
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST, request.FILES)
        if user_form.is_valid():
            user_type = user_form.cleaned_data['user_type']
            
            # Determine which profile form to use based on user type
            if user_type == 'PATIENT':
                profile_form = PatientProfileForm(request.POST)
            elif user_type == 'DOCTOR':
                profile_form = DoctorProfileForm(request.POST)
            elif user_type == 'NURSE':
                profile_form = NurseProfileForm(request.POST)
            elif user_type == 'PHARMACIST':
                profile_form = PharmacistProfileForm(request.POST)
            elif user_type == 'LAB_TECH':
                profile_form = LabTechnicianProfileForm(request.POST)
            else:
                # No profile form needed for admin and insurance
                profile_form = None
            
            # Check if profile form is valid
            if profile_form is None or profile_form.is_valid():
                with transaction.atomic():
                    # Save user first
                    user = user_form.save()
                    
                    # Then create and link profile if needed
                    if profile_form:
                        profile = profile_form.save(commit=False)
                        profile.user = user
                        profile.save()
                    
                    # Login the user and redirect
                    login(request, user)
                    messages.success(request, "Registration successful!")
                    
                    # Redirect based on user type
                    if user_type == 'PATIENT':
                        return redirect('patient:dashboard')
                    elif user_type == 'DOCTOR':
                        return redirect('doctor:dashboard')
                    elif user_type == 'NURSE':
                        return redirect('doctor:dashboard')  # Nurses use doctor dashboard
                    elif user_type == 'ADMIN':
                        return redirect('admin_panel:dashboard')
                    elif user_type == 'PHARMACIST':
                        return redirect('pharmacy:dashboard')
                    elif user_type == 'INSURANCE':
                        return redirect('insurance:dashboard')
                    elif user_type == 'LAB_TECH':
                        return redirect('laboratory:dashboard')
                    else:
                        return redirect('home')
        else:
            messages.error(request, "Registration failed. Please check the form.")
    else:
        user_form = UserRegistrationForm()
    
    # Default profile form is PatientProfileForm, will be replaced by JavaScript
    profile_form = PatientProfileForm()
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'patient_form': PatientProfileForm(),
        'doctor_form': DoctorProfileForm(),
        'nurse_form': NurseProfileForm(),
        'pharmacist_form': PharmacistProfileForm(),
        'lab_tech_form': LabTechnicianProfileForm(),
    }
    return render(request, 'accounts/register.html', context)

def login_view(request):
    """User login view."""
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=email, password=password)
            
            if user is not None:
                login(request, user)
                messages.info(request, f"You are logged in as {user.get_full_name()}.")
                
                # Redirect based on user type
                if user.user_type == 'PATIENT':
                    return redirect('patient:dashboard')
                elif user.user_type == 'DOCTOR':
                    return redirect('doctor:dashboard')
                elif user.user_type == 'NURSE':
                    return redirect('doctor:dashboard')  # Nurses use doctor dashboard
                elif user.user_type == 'ADMIN':
                    return redirect('admin_panel:dashboard')
                elif user.user_type == 'PHARMACIST':
                    return redirect('pharmacy:dashboard')
                elif user.user_type == 'INSURANCE':
                    return redirect('insurance:dashboard')
                elif user.user_type == 'LAB_TECH':
                    return redirect('laboratory:dashboard')
                else:
                    return redirect('home')
            else:
                messages.error(request, "Invalid email or password.")
        else:
            messages.error(request, "Invalid email or password.")
    else:
        form = CustomAuthenticationForm()
    
    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    """User logout view."""
    logout(request)
    messages.info(request, "You have successfully logged out.")
    return redirect('home')

@login_required
def profile_view(request):
    """User profile view."""
    user = request.user
    profile = user.get_role_specific_profile()
    
    if request.method == 'POST':
        # Process user form update
        user_form = UserRegistrationForm(request.POST, request.FILES, instance=user)
        
        # Determine which profile form to use
        if user.user_type == 'PATIENT':
            profile_form = PatientProfileForm(request.POST, instance=profile)
        elif user.user_type == 'DOCTOR':
            profile_form = DoctorProfileForm(request.POST, instance=profile)
        elif user.user_type == 'NURSE':
            profile_form = NurseProfileForm(request.POST, instance=profile)
        elif user.user_type == 'PHARMACIST':
            profile_form = PharmacistProfileForm(request.POST, instance=profile)
        elif user.user_type == 'LAB_TECH':
            profile_form = LabTechnicianProfileForm(request.POST, instance=profile)
        else:
            profile_form = None
        
        # Save user and profile if valid
        if user_form.is_valid() and (profile_form is None or profile_form.is_valid()):
            with transaction.atomic():
                user_form.save()
                if profile_form:
                    profile_form.save()
            
            messages.success(request, "Profile updated successfully!")
            return redirect('profile')
        else:
            messages.error(request, "Error updating profile.")
    else:
        user_form = UserRegistrationForm(instance=user)
        
        # Initialize the appropriate profile form
        if user.user_type == 'PATIENT':
            profile_form = PatientProfileForm(instance=profile)
        elif user.user_type == 'DOCTOR':
            profile_form = DoctorProfileForm(instance=profile)
        elif user.user_type == 'NURSE':
            profile_form = NurseProfileForm(instance=profile)
        elif user.user_type == 'PHARMACIST':
            profile_form = PharmacistProfileForm(instance=profile)
        elif user.user_type == 'LAB_TECH':
            profile_form = LabTechnicianProfileForm(instance=profile)
        else:
            profile_form = None
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'user': user,
        'profile': profile,
    }
    return render(request, 'accounts/profile.html', context)