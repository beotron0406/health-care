# patient/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q
from django.core.paginator import Paginator

from accounts.models import User, DoctorProfile, PatientProfile
from .models import (
    MedicalRecord, Appointment, Prescription, 
    PrescriptionItem, Bill, Insurance, InsuranceClaim
)
from .forms import (
    AppointmentForm, MedicalRecordForm, 
    InsuranceForm, BillPaymentForm
)

@login_required
def dashboard(request):
    """Patient dashboard view"""
    if request.user.user_type != 'PATIENT':
        messages.error(request, "Access denied. Patient access only.")
        return redirect('accounts:home')
    
    # Get patient profile
    patient_profile = get_object_or_404(PatientProfile, user=request.user)
    
    # Get recent appointments
    upcoming_appointments = Appointment.objects.filter(
        patient=patient_profile,
        appointment_date__gte=timezone.now().date(),
        status='SCHEDULED'
    ).order_by('appointment_date', 'appointment_time')[:5]
    
    # Get recent prescriptions
    recent_prescriptions = Prescription.objects.filter(
        patient=patient_profile,
        is_active=True
    ).order_by('-date_prescribed')[:5]
    
    # Get recent medical records
    recent_medical_records = MedicalRecord.objects.filter(
        patient=patient_profile
    ).order_by('-date_created')[:5]
    
    # Get pending bills
    pending_bills = Bill.objects.filter(
        patient=patient_profile,
        status='PENDING'
    ).order_by('due_date')[:5]
    
    context = {
        'patient': patient_profile,
        'upcoming_appointments': upcoming_appointments,
        'recent_prescriptions': recent_prescriptions,
        'recent_medical_records': recent_medical_records,
        'pending_bills': pending_bills,
    }
    
    return render(request, 'patient/dashboard.html', context)

@login_required
def appointments(request):
    """View for managing patient appointments"""
    if request.user.user_type != 'PATIENT':
        messages.error(request, "Access denied. Patient access only.")
        return redirect('accounts:home')
    
    patient_profile = get_object_or_404(PatientProfile, user=request.user)
    
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.patient = patient_profile
            appointment.status = 'SCHEDULED'
            appointment.save()
            messages.success(request, "Appointment scheduled successfully!")
            return redirect('patient:appointments')
    else:
        form = AppointmentForm()
    
    # Get all appointments for the patient
    all_appointments = Appointment.objects.filter(patient=patient_profile).order_by('-appointment_date')
    
    # Pagination
    paginator = Paginator(all_appointments, 10)  # Show 10 appointments per page
    page_number = request.GET.get('page')
    appointments = paginator.get_page(page_number)
    
    # Get all available doctors for the form
    doctors = DoctorProfile.objects.all()
    
    context = {
        'appointments': appointments,
        'form': form,
        'doctors': doctors,
        'patient': patient_profile,
    }
    
    return render(request, 'patient/appointments.html', context)

@login_required
def appointment_detail(request, pk):
    """View for appointment details"""
    if request.user.user_type != 'PATIENT':
        messages.error(request, "Access denied. Patient access only.")
        return redirect('accounts:home')
    
    patient_profile = get_object_or_404(PatientProfile, user=request.user)
    appointment = get_object_or_404(Appointment, pk=pk, patient=patient_profile)
    
    context = {
        'appointment': appointment,
        'patient': patient_profile,
    }
    
    return render(request, 'patient/appointment_detail.html', context)

@login_required
def cancel_appointment(request, pk):
    """View for cancelling an appointment"""
    if request.user.user_type != 'PATIENT':
        messages.error(request, "Access denied. Patient access only.")
        return redirect('accounts:home')
    
    patient_profile = get_object_or_404(PatientProfile, user=request.user)
    appointment = get_object_or_404(Appointment, pk=pk, patient=patient_profile)
    
    # Check if appointment is upcoming and can be cancelled
    if appointment.appointment_date < timezone.now().date():
        messages.error(request, "Cannot cancel past appointments.")
        return redirect('patient:appointment_detail', pk=pk)
    
    if appointment.status != 'SCHEDULED':
        messages.error(request, f"Cannot cancel appointment with status: {appointment.get_status_display()}")
        return redirect('patient:appointment_detail', pk=pk)
    
    if request.method == 'POST':
        appointment.status = 'CANCELLED'
        appointment.save()
        messages.success(request, "Appointment cancelled successfully.")
        return redirect('patient:appointments')
    
    context = {
        'appointment': appointment,
        'patient': patient_profile,
    }
    
    return render(request, 'patient/cancel_appointment.html', context)

@login_required
def medical_records(request):
    """View for patient medical records"""
    if request.user.user_type != 'PATIENT':
        messages.error(request, "Access denied. Patient access only.")
        return redirect('accounts:home')
    
    patient_profile = get_object_or_404(PatientProfile, user=request.user)
    
    # Get all medical records for the patient
    all_records = MedicalRecord.objects.filter(patient=patient_profile).order_by('-date_created')
    
    # Pagination
    paginator = Paginator(all_records, 10)  # Show 10 records per page
    page_number = request.GET.get('page')
    records = paginator.get_page(page_number)
    
    context = {
        'records': records,
        'patient': patient_profile,
    }
    
    return render(request, 'patient/medical_records.html', context)

@login_required
def medical_record_detail(request, pk):
    """View for medical record details"""
    if request.user.user_type != 'PATIENT':
        messages.error(request, "Access denied. Patient access only.")
        return redirect('accounts:home')
    
    patient_profile = get_object_or_404(PatientProfile, user=request.user)
    record = get_object_or_404(MedicalRecord, pk=pk, patient=patient_profile)
    
    # Get prescriptions associated with this medical record
    prescriptions = Prescription.objects.filter(medical_record=record)
    
    context = {
        'record': record,
        'patient': patient_profile,
        'prescriptions': prescriptions,
    }
    
    return render(request, 'patient/medical_record_detail.html', context)

@login_required
def prescriptions(request):
    """View for patient prescriptions"""
    if request.user.user_type != 'PATIENT':
        messages.error(request, "Access denied. Patient access only.")
        return redirect('accounts:home')
    
    patient_profile = get_object_or_404(PatientProfile, user=request.user)
    
    # Get all prescriptions for the patient
    all_prescriptions = Prescription.objects.filter(patient=patient_profile).order_by('-date_prescribed')
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter == 'active':
        all_prescriptions = all_prescriptions.filter(is_active=True)
    elif status_filter == 'inactive':
        all_prescriptions = all_prescriptions.filter(is_active=False)
    
    # Pagination
    paginator = Paginator(all_prescriptions, 10)  # Show 10 prescriptions per page
    page_number = request.GET.get('page')
    prescriptions = paginator.get_page(page_number)
    
    context = {
        'prescriptions': prescriptions,
        'patient': patient_profile,
        'status_filter': status_filter,
    }
    
    return render(request, 'patient/prescriptions.html', context)

@login_required
def prescription_detail(request, pk):
    """View for prescription details"""
    if request.user.user_type != 'PATIENT':
        messages.error(request, "Access denied. Patient access only.")
        return redirect('accounts:home')
    
    patient_profile = get_object_or_404(PatientProfile, user=request.user)
    prescription = get_object_or_404(Prescription, pk=pk, patient=patient_profile)
    
    # Get all medicine items in the prescription
    prescription_items = PrescriptionItem.objects.filter(prescription=prescription)
    
    # Check if there's a bill associated with this prescription
    try:
        bill = Bill.objects.get(prescription=prescription)
    except Bill.DoesNotExist:
        bill = None
    
    context = {
        'prescription': prescription,
        'prescription_items': prescription_items,
        'patient': patient_profile,
        'bill': bill,
    }
    
    return render(request, 'patient/prescription_detail.html', context)

@login_required
def bills(request):
    """View for patient bills"""
    if request.user.user_type != 'PATIENT':
        messages.error(request, "Access denied. Patient access only.")
        return redirect('accounts:home')
    
    patient_profile = get_object_or_404(PatientProfile, user=request.user)
    
    # Get all bills for the patient
    all_bills = Bill.objects.filter(patient=patient_profile).order_by('-created_at')
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter:
        all_bills = all_bills.filter(status=status_filter.upper())
    
    # Pagination
    paginator = Paginator(all_bills, 10)  # Show 10 bills per page
    page_number = request.GET.get('page')
    bills = paginator.get_page(page_number)
    
    context = {
        'bills': bills,
        'patient': patient_profile,
        'status_filter': status_filter,
    }
    
    return render(request, 'patient/bills.html', context)

@login_required
def bill_detail(request, pk):
    """View for bill details and payment"""
    if request.user.user_type != 'PATIENT':
        messages.error(request, "Access denied. Patient access only.")
        return redirect('accounts:home')
    
    patient_profile = get_object_or_404(PatientProfile, user=request.user)
    bill = get_object_or_404(Bill, pk=pk, patient=patient_profile)
    
    if request.method == 'POST':
        form = BillPaymentForm(request.POST, instance=bill)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.status = 'PAID'
            payment.payment_date = timezone.now()
            payment.save()
            messages.success(request, "Payment processed successfully!")
            return redirect('patient:bill_detail', pk=pk)
    else:
        form = BillPaymentForm(instance=bill)
    
    # Get insurance claims associated with this bill
    insurance_claims = InsuranceClaim.objects.filter(bill=bill)
    
    context = {
        'bill': bill,
        'patient': patient_profile,
        'form': form,
        'insurance_claims': insurance_claims,
    }
    
    return render(request, 'patient/bill_detail.html', context)

@login_required
def insurance(request):
    """View for patient insurance information"""
    if request.user.user_type != 'PATIENT':
        messages.error(request, "Access denied. Patient access only.")
        return redirect('accounts:home')
    
    patient_profile = get_object_or_404(PatientProfile, user=request.user)
    
    if request.method == 'POST':
        form = InsuranceForm(request.POST)
        if form.is_valid():
            insurance = form.save(commit=False)
            insurance.patient = patient_profile
            insurance.save()
            messages.success(request, "Insurance information added successfully!")
            return redirect('patient:insurance')
    else:
        form = InsuranceForm()
    
    # Get all insurance entries for the patient
    insurances = Insurance.objects.filter(patient=patient_profile).order_by('-coverage_start_date')
    
    context = {
        'insurances': insurances,
        'patient': patient_profile,
        'form': form,
    }
    
    return render(request, 'patient/insurance.html', context)

@login_required
def submit_insurance_claim(request, bill_id):
    """View for submitting an insurance claim for a bill"""
    if request.user.user_type != 'PATIENT':
        messages.error(request, "Access denied. Patient access only.")
        return redirect('accounts:home')
    
    patient_profile = get_object_or_404(PatientProfile, user=request.user)
    bill = get_object_or_404(Bill, pk=bill_id, patient=patient_profile)
    
    # Check if bill is eligible for insurance claim
    if bill.status != 'PENDING' and bill.status != 'PAID':
        messages.error(request, "Only pending or paid bills can be submitted for insurance claim.")
        return redirect('patient:bill_detail', pk=bill_id)
    
    # Check if bill already has an insurance claim
    if InsuranceClaim.objects.filter(bill=bill).exists():
        messages.error(request, "An insurance claim already exists for this bill.")
        return redirect('patient:bill_detail', pk=bill_id)
    
    # Get active insurance policies for the patient
    active_insurances = Insurance.objects.filter(
        patient=patient_profile,
        is_active=True,
        coverage_end_date__gte=timezone.now().date()
    )
    
    if request.method == 'POST':
        insurance_id = request.POST.get('insurance')
        amount_claimed = request.POST.get('amount_claimed')
        notes = request.POST.get('notes', '')
        
        try:
            insurance = Insurance.objects.get(pk=insurance_id, patient=patient_profile)
            
            # Create claim number (simple implementation)
            claim_number = f"CLM-{timezone.now().strftime('%Y%m%d')}-{bill.id}"
            
            # Create insurance claim
            claim = InsuranceClaim.objects.create(
                insurance=insurance,
                bill=bill,
                claim_number=claim_number,
                amount_claimed=amount_claimed,
                notes=notes,
                status='SUBMITTED'
            )
            
            messages.success(request, f"Insurance claim submitted successfully! Claim Number: {claim_number}")
            return redirect('patient:bill_detail', pk=bill_id)
            
        except (Insurance.DoesNotExist, ValueError) as e:
            messages.error(request, f"Error submitting insurance claim: {str(e)}")
    
    context = {
        'bill': bill,
        'patient': patient_profile,
        'insurances': active_insurances,
    }
    
    return render(request, 'patient/submit_insurance_claim.html', context)

@login_required
def search_doctors(request):
    """View for searching doctors by name, specialization, etc."""
    if request.user.user_type != 'PATIENT':
        messages.error(request, "Access denied. Patient access only.")
        return redirect('accounts:home')
    
    query = request.GET.get('q', '')
    specialization = request.GET.get('specialization', '')
    
    doctors = DoctorProfile.objects.all()
    
    if query:
        doctors = doctors.filter(
            Q(user__first_name__icontains=query) | 
            Q(user__last_name__icontains=query) |
            Q(specialization__icontains=query)
        )
    
    if specialization:
        doctors = doctors.filter(specialization__icontains=specialization)
    
    # Get list of unique specializations for filtering
    all_specializations = DoctorProfile.objects.values_list('specialization', flat=True).distinct()
    
    context = {
        'doctors': doctors,
        'query': query,
        'specialization': specialization,
        'all_specializations': all_specializations,
    }
    
    return render(request, 'patient/search_doctors.html', context)