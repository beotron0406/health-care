# doctor/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q
from django.core.paginator import Paginator

from accounts.models import User, DoctorProfile, PatientProfile, NurseProfile
from patient.models import (
    MedicalRecord, Appointment, Prescription, 
    PrescriptionItem, Medicine, Bill
)
from .models import (
    DoctorSchedule, DoctorLeave, Treatment, 
    PatientNote, Referral, Task, NurseAssignment,
    DoctorAvailableTimeSlot
)
from .forms import (
    DoctorScheduleForm, DoctorLeaveForm, MedicalRecordForm, 
    TreatmentForm, PatientNoteForm, ReferralForm,
    TaskForm, NurseAssignmentForm, AppointmentUpdateForm,
    PrescriptionForm, PrescriptionItemForm, DoctorAvailableTimeSlotForm
)

@login_required
def dashboard(request):
    """Doctor dashboard view"""
    if request.user.user_type not in ['DOCTOR', 'NURSE']:
        messages.error(request, "Access denied. Doctor or Nurse access only.")
        return redirect('accounts:home')
    
    # Get doctor profile or associated doctor for nurse
    if request.user.user_type == 'DOCTOR':
        doctor_profile = get_object_or_404(DoctorProfile, user=request.user)
        context = {'is_doctor': True, 'profile': doctor_profile}
    else:  # Nurse
        nurse_profile = get_object_or_404(NurseProfile, user=request.user)
        # Get the doctor this nurse is assigned to (assuming one doctor per nurse for simplicity)
        assignment = NurseAssignment.objects.filter(nurse=nurse_profile, is_active=True).first()
        if assignment:
            doctor_profile = assignment.doctor
            context = {'is_doctor': False, 'is_nurse': True, 'nurse_profile': nurse_profile, 'doctor_profile': doctor_profile}
        else:
            messages.warning(request, "You're not currently assigned to any doctor.")
            context = {'is_doctor': False, 'is_nurse': True, 'nurse_profile': nurse_profile}
            return render(request, 'doctor/dashboard.html', context)
    
    # Today's appointments
    today = timezone.now().date()
    today_appointments = Appointment.objects.filter(
        doctor=doctor_profile,
        appointment_date=today
    ).order_by('appointment_time')
    
    # Upcoming appointments (excluding today)
    upcoming_appointments = Appointment.objects.filter(
        doctor=doctor_profile,
        appointment_date__gt=today,
        status='SCHEDULED'
    ).order_by('appointment_date', 'appointment_time')[:5]
    
    # Recent medical records
    recent_records = MedicalRecord.objects.filter(
        doctor=doctor_profile
    ).order_by('-date_created')[:5]
    
    # Tasks (for both doctors and nurses)
    if request.user.user_type == 'DOCTOR':
        # Tasks created by the doctor
        tasks = Task.objects.filter(
            doctor=doctor_profile
        ).order_by('status', 'priority', 'due_date')[:5]
    else:  # Nurse
        # Tasks assigned to the nurse
        tasks = Task.objects.filter(
            assigned_to=request.user
        ).order_by('status', 'priority', 'due_date')[:5]
    
    # Add to context
    context.update({
        'today_appointments': today_appointments,
        'upcoming_appointments': upcoming_appointments,
        'recent_records': recent_records,
        'tasks': tasks,
        'today': today,
    })
    
    return render(request, 'doctor/dashboard.html', context)

@login_required
def appointments(request):
    """View for managing doctor's appointments"""
    if request.user.user_type not in ['DOCTOR', 'NURSE']:
        messages.error(request, "Access denied. Doctor or Nurse access only.")
        return redirect('accounts:home')
    
    # Get doctor profile
    if request.user.user_type == 'DOCTOR':
        doctor_profile = get_object_or_404(DoctorProfile, user=request.user)
    else:  # Nurse
        nurse_profile = get_object_or_404(NurseProfile, user=request.user)
        assignment = NurseAssignment.objects.filter(nurse=nurse_profile, is_active=True).first()
        if assignment:
            doctor_profile = assignment.doctor
        else:
            messages.warning(request, "You're not currently assigned to any doctor.")
            return redirect('doctor:dashboard')
    
    # Handle filters
    status_filter = request.GET.get('status', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    patient_filter = request.GET.get('patient', '')
    
    # Base queryset
    appointments = Appointment.objects.filter(doctor=doctor_profile).order_by('-appointment_date', '-appointment_time')
    
    # Apply filters
    if status_filter:
        appointments = appointments.filter(status=status_filter)
    
    if date_from:
        appointments = appointments.filter(appointment_date__gte=date_from)
    
    if date_to:
        appointments = appointments.filter(appointment_date__lte=date_to)
    
    if patient_filter:
        appointments = appointments.filter(
            Q(patient__user__first_name__icontains=patient_filter) | 
            Q(patient__user__last_name__icontains=patient_filter)
        )
    
    # Pagination
    paginator = Paginator(appointments, 10)  # Show 10 appointments per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'appointments': page_obj,
        'status_filter': status_filter,
        'date_from': date_from,
        'date_to': date_to,
        'patient_filter': patient_filter,
        'is_doctor': request.user.user_type == 'DOCTOR',
        'is_nurse': request.user.user_type == 'NURSE',
    }
    
    return render(request, 'doctor/appointments.html', context)

@login_required
def appointment_detail(request, pk):
    """View for appointment details and update"""
    if request.user.user_type not in ['DOCTOR', 'NURSE']:
        messages.error(request, "Access denied. Doctor or Nurse access only.")
        return redirect('accounts:home')
    
    # Get doctor profile
    if request.user.user_type == 'DOCTOR':
        doctor_profile = get_object_or_404(DoctorProfile, user=request.user)
    else:  # Nurse
        nurse_profile = get_object_or_404(NurseProfile, user=request.user)
        assignment = NurseAssignment.objects.filter(nurse=nurse_profile, is_active=True).first()
        if assignment:
            doctor_profile = assignment.doctor
        else:
            messages.warning(request, "You're not currently assigned to any doctor.")
            return redirect('doctor:dashboard')
    
    # Get appointment
    appointment = get_object_or_404(Appointment, pk=pk, doctor=doctor_profile)
    
    if request.method == 'POST':
        form = AppointmentUpdateForm(request.POST, instance=appointment)
        if form.is_valid():
            form.save()
            messages.success(request, "Appointment updated successfully")
            return redirect('doctor:appointment_detail', pk=pk)
    else:
        form = AppointmentUpdateForm(instance=appointment)
    
    # Get patient's medical records
    medical_records = MedicalRecord.objects.filter(
        patient=appointment.patient
    ).order_by('-date_created')
    
    # Get patient's prescriptions
    prescriptions = Prescription.objects.filter(
        patient=appointment.patient
    ).order_by('-date_prescribed')
    
    context = {
        'appointment': appointment,
        'form': form,
        'medical_records': medical_records,
        'prescriptions': prescriptions,
        'is_doctor': request.user.user_type == 'DOCTOR',
        'is_nurse': request.user.user_type == 'NURSE',
    }
    
    return render(request, 'doctor/appointment_detail.html', context)

@login_required
def create_medical_record(request, appointment_id):
    """View for creating a new medical record for an appointment"""
    if request.user.user_type != 'DOCTOR':
        messages.error(request, "Access denied. Doctor access only.")
        return redirect('accounts:home')
    
    doctor_profile = get_object_or_404(DoctorProfile, user=request.user)
    appointment = get_object_or_404(Appointment, pk=appointment_id, doctor=doctor_profile)
    
    if request.method == 'POST':
        med_record_form = MedicalRecordForm(request.POST)
        treatment_form = TreatmentForm(request.POST)
        
        if med_record_form.is_valid() and treatment_form.is_valid():
            # Save medical record
            medical_record = med_record_form.save(commit=False)
            medical_record.doctor = doctor_profile
            medical_record.patient = appointment.patient
            medical_record.save()
            
            # Save treatment
            treatment = treatment_form.save(commit=False)
            treatment.medical_record = medical_record
            treatment.save()
            
            # Update appointment status
            appointment.status = 'COMPLETED'
            appointment.save()
            
            messages.success(request, "Medical record created successfully")
            return redirect('doctor:medical_record_detail', pk=medical_record.id)
    else:
        med_record_form = MedicalRecordForm()
        treatment_form = TreatmentForm()
    
    context = {
        'appointment': appointment,
        'med_record_form': med_record_form,
        'treatment_form': treatment_form,
    }
    
    return render(request, 'doctor/create_medical_record.html', context)

@login_required
def medical_records(request):
    """View for doctor's medical records"""
    if request.user.user_type not in ['DOCTOR', 'NURSE']:
        messages.error(request, "Access denied. Doctor or Nurse access only.")
        return redirect('accounts:home')
    
    # Get doctor profile
    if request.user.user_type == 'DOCTOR':
        doctor_profile = get_object_or_404(DoctorProfile, user=request.user)
    else:  # Nurse
        nurse_profile = get_object_or_404(NurseProfile, user=request.user)
        assignment = NurseAssignment.objects.filter(nurse=nurse_profile, is_active=True).first()
        if assignment:
            doctor_profile = assignment.doctor
        else:
            messages.warning(request, "You're not currently assigned to any doctor.")
            return redirect('doctor:dashboard')
    
    # Handle filters
    patient_filter = request.GET.get('patient', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # Base queryset
    records = MedicalRecord.objects.filter(doctor=doctor_profile).order_by('-date_created')
    
    # Apply filters
    if patient_filter:
        records = records.filter(
            Q(patient__user__first_name__icontains=patient_filter) | 
            Q(patient__user__last_name__icontains=patient_filter)
        )
    
    if date_from:
        records = records.filter(date_created__date__gte=date_from)
    
    if date_to:
        records = records.filter(date_created__date__lte=date_to)
    
    # Pagination
    paginator = Paginator(records, 10)  # Show 10 records per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'records': page_obj,
        'patient_filter': patient_filter,
        'date_from': date_from,
        'date_to': date_to,
        'is_doctor': request.user.user_type == 'DOCTOR',
        'is_nurse': request.user.user_type == 'NURSE',
    }
    
    return render(request, 'doctor/medical_records.html', context)

@login_required
def medical_record_detail(request, pk):
    """View for medical record details"""
    if request.user.user_type not in ['DOCTOR', 'NURSE']:
        messages.error(request, "Access denied. Doctor or Nurse access only.")
        return redirect('accounts:home')
    
    # Get doctor profile
    if request.user.user_type == 'DOCTOR':
        doctor_profile = get_object_or_404(DoctorProfile, user=request.user)
    else:  # Nurse
        nurse_profile = get_object_or_404(NurseProfile, user=request.user)
        assignment = NurseAssignment.objects.filter(nurse=nurse_profile, is_active=True).first()
        if assignment:
            doctor_profile = assignment.doctor
        else:
            messages.warning(request, "You're not currently assigned to any doctor.")
            return redirect('doctor:dashboard')
    
    # Get medical record
    record = get_object_or_404(MedicalRecord, pk=pk, doctor=doctor_profile)
    
    # Get prescriptions associated with this record
    try:
        prescriptions = Prescription.objects.filter(medical_record=record)
    except:
        prescriptions = []
    
    # Get treatment plan if exists
    try:
        treatment = Treatment.objects.get(medical_record=record)
    except Treatment.DoesNotExist:
        treatment = None
    
    context = {
        'record': record,
        'treatment': treatment,
        'prescriptions': prescriptions,
        'is_doctor': request.user.user_type == 'DOCTOR',
        'is_nurse': request.user.user_type == 'NURSE',
    }
    
    return render(request, 'doctor/medical_record_detail.html', context)

@login_required
def edit_medical_record(request, pk):
    """View for editing a medical record"""
    if request.user.user_type != 'DOCTOR':
        messages.error(request, "Access denied. Doctor access only.")
        return redirect('accounts:home')
    
    doctor_profile = get_object_or_404(DoctorProfile, user=request.user)
    record = get_object_or_404(MedicalRecord, pk=pk, doctor=doctor_profile)
    
    try:
        treatment = Treatment.objects.get(medical_record=record)
    except Treatment.DoesNotExist:
        treatment = None
    
    if request.method == 'POST':
        med_record_form = MedicalRecordForm(request.POST, instance=record)
        
        if treatment:
            treatment_form = TreatmentForm(request.POST, instance=treatment)
        else:
            treatment_form = TreatmentForm(request.POST)
        
        if med_record_form.is_valid() and treatment_form.is_valid():
            med_record_form.save()
            
            if not treatment:
                treatment = treatment_form.save(commit=False)
                treatment.medical_record = record
                treatment.save()
            else:
                treatment_form.save()
            
            messages.success(request, "Medical record updated successfully")
            return redirect('doctor:medical_record_detail', pk=pk)
    else:
        med_record_form = MedicalRecordForm(instance=record)
        treatment_form = TreatmentForm(instance=treatment) if treatment else TreatmentForm()
    
    context = {
        'record': record,
        'med_record_form': med_record_form,
        'treatment_form': treatment_form,
    }
    
    return render(request, 'doctor/edit_medical_record.html', context)

@login_required
def create_prescription(request, record_id=None, patient_id=None):
    """View for creating a new prescription"""
    if request.user.user_type != 'DOCTOR':
        messages.error(request, "Access denied. Doctor access only.")
        return redirect('accounts:home')
    
    doctor_profile = get_object_or_404(DoctorProfile, user=request.user)
    
    # Determine patient and medical record based on provided IDs
    if record_id:
        medical_record = get_object_or_404(MedicalRecord, pk=record_id, doctor=doctor_profile)
        patient = medical_record.patient
    elif patient_id:
        patient = get_object_or_404(PatientProfile, pk=patient_id)
        medical_record = None
    else:
        messages.error(request, "Missing patient or medical record information")
        return redirect('doctor:dashboard')
    
    if request.method == 'POST':
        form = PrescriptionForm(request.POST)
        
        if form.is_valid():
            prescription = form.save(commit=False)
            prescription.doctor = doctor_profile
            prescription.patient = patient
            prescription.medical_record = medical_record
            prescription.save()
            
            messages.success(request, "Prescription created successfully. Add medicines to it.")
            return redirect('doctor:edit_prescription', pk=prescription.id)
    else:
        form = PrescriptionForm()
    
    context = {
        'form': form,
        'patient': patient,
        'medical_record': medical_record,
    }
    
    return render(request, 'doctor/create_prescription.html', context)

@login_required
def edit_prescription(request, pk):
    """View for editing/adding medicines to a prescription"""
    if request.user.user_type != 'DOCTOR':
        messages.error(request, "Access denied. Doctor access only.")
        return redirect('accounts:home')
    
    doctor_profile = get_object_or_404(DoctorProfile, user=request.user)
    prescription = get_object_or_404(Prescription, pk=pk, doctor=doctor_profile)
    
    if request.method == 'POST':
        if 'add_medicine' in request.POST:
            medicine_form = PrescriptionItemForm(request.POST)
            if medicine_form.is_valid():
                medicine_item = medicine_form.save(commit=False)
                medicine_item.prescription = prescription
                medicine_item.save()
                
                messages.success(request, "Medicine added to prescription")
                return redirect('doctor:edit_prescription', pk=pk)
        else:
            prescription_form = PrescriptionForm(request.POST, instance=prescription)
            if prescription_form.is_valid():
                prescription_form.save()
                messages.success(request, "Prescription updated successfully")
                return redirect('doctor:prescription_detail', pk=pk)
    else:
        prescription_form = PrescriptionForm(instance=prescription)
        medicine_form = PrescriptionItemForm()
    
    # Get all medicine items in the prescription
    prescription_items = PrescriptionItem.objects.filter(prescription=prescription)
    
    context = {
        'prescription': prescription,
        'prescription_form': prescription_form,
        'medicine_form': medicine_form,
        'prescription_items': prescription_items,
    }
    
    return render(request, 'doctor/edit_prescription.html', context)

@login_required
def prescription_detail(request, pk):
    """View for prescription details"""
    if request.user.user_type not in ['DOCTOR', 'NURSE']:
        messages.error(request, "Access denied. Doctor or Nurse access only.")
        return redirect('accounts:home')
    
    # Get doctor profile
    if request.user.user_type == 'DOCTOR':
        doctor_profile = get_object_or_404(DoctorProfile, user=request.user)
    else:  # Nurse
        nurse_profile = get_object_or_404(NurseProfile, user=request.user)
        assignment = NurseAssignment.objects.filter(nurse=nurse_profile, is_active=True).first()
        if assignment:
            doctor_profile = assignment.doctor
        else:
            messages.warning(request, "You're not currently assigned to any doctor.")
            return redirect('doctor:dashboard')
    
    # Get prescription
    prescription = get_object_or_404(Prescription, pk=pk, doctor=doctor_profile)
    
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
        'bill': bill,
        'is_doctor': request.user.user_type == 'DOCTOR',
        'is_nurse': request.user.user_type == 'NURSE',
    }
    
    return render(request, 'doctor/prescription_detail.html', context)

@login_required
def prescriptions(request):
    """View for doctor's prescriptions"""
    if request.user.user_type not in ['DOCTOR', 'NURSE']:
        messages.error(request, "Access denied. Doctor or Nurse access only.")
        return redirect('accounts:home')
    
    # Get doctor profile
    if request.user.user_type == 'DOCTOR':
        doctor_profile = get_object_or_404(DoctorProfile, user=request.user)
    else:  # Nurse
        nurse_profile = get_object_or_404(NurseProfile, user=request.user)
        assignment = NurseAssignment.objects.filter(nurse=nurse_profile, is_active=True).first()
        if assignment:
            doctor_profile = assignment.doctor
        else:
            messages.warning(request, "You're not currently assigned to any doctor.")
            return redirect('doctor:dashboard')
    
    # Handle filters
    patient_filter = request.GET.get('patient', '')
    status_filter = request.GET.get('status', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # Base queryset
    prescriptions = Prescription.objects.filter(doctor=doctor_profile).order_by('-date_prescribed')
    
    # Apply filters
    if patient_filter:
        prescriptions = prescriptions.filter(
            Q(patient__user__first_name__icontains=patient_filter) | 
            Q(patient__user__last_name__icontains=patient_filter)
        )
    
    if status_filter:
        if status_filter == 'active':
            prescriptions = prescriptions.filter(is_active=True)
        elif status_filter == 'inactive':
            prescriptions = prescriptions.filter(is_active=False)
    
    if date_from:
        prescriptions = prescriptions.filter(date_prescribed__gte=date_from)
    
    if date_to:
        prescriptions = prescriptions.filter(date_prescribed__lte=date_to)
    
    # Pagination
    paginator = Paginator(prescriptions, 10)  # Show 10 prescriptions per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'prescriptions': page_obj,
        'patient_filter': patient_filter,
        'status_filter': status_filter,
        'date_from': date_from,
        'date_to': date_to,
        'is_doctor': request.user.user_type == 'DOCTOR',
        'is_nurse': request.user.user_type == 'NURSE',
    }
    
    return render(request, 'doctor/prescriptions.html', context)

@login_required
def patients(request):
    """View for managing patients"""
    if request.user.user_type not in ['DOCTOR', 'NURSE']:
        messages.error(request, "Access denied. Doctor or Nurse access only.")
        return redirect('accounts:home')
    
    # Get doctor profile
    if request.user.user_type == 'DOCTOR':
        doctor_profile = get_object_or_404(DoctorProfile, user=request.user)
    else:  # Nurse
        nurse_profile = get_object_or_404(NurseProfile, user=request.user)
        assignment = NurseAssignment.objects.filter(nurse=nurse_profile, is_active=True).first()
        if assignment:
            doctor_profile = assignment.doctor
        else:
            messages.warning(request, "You're not currently assigned to any doctor.")
            return redirect('doctor:dashboard')
    
    # Search filter
    search = request.GET.get('search', '')
    
    # Get all unique patients who have had appointments with this doctor
    patient_ids = Appointment.objects.filter(doctor=doctor_profile).values_list('patient_id', flat=True).distinct()
    patients = PatientProfile.objects.filter(id__in=patient_ids)
    
    # Apply search filter if provided
    if search:
        patients = patients.filter(
            Q(user__first_name__icontains=search) | 
            Q(user__last_name__icontains=search) |
            Q(user__email__icontains=search)
        )
    
    # Pagination
    paginator = Paginator(patients, 10)  # Show 10 patients per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'patients': page_obj,
        'search': search,
        'is_doctor': request.user.user_type == 'DOCTOR',
        'is_nurse': request.user.user_type == 'NURSE',
    }
    
    return render(request, 'doctor/patients.html', context)

@login_required
def patient_detail(request, pk):
    """View for patient details"""
    if request.user.user_type not in ['DOCTOR', 'NURSE']:
        messages.error(request, "Access denied. Doctor or Nurse access only.")
        return redirect('accounts:home')
    
    # Get doctor profile
    if request.user.user_type == 'DOCTOR':
        doctor_profile = get_object_or_404(DoctorProfile, user=request.user)
    else:  # Nurse
        nurse_profile = get_object_or_404(NurseProfile, user=request.user)
        assignment = NurseAssignment.objects.filter(nurse=nurse_profile, is_active=True).first()
        if assignment:
            doctor_profile = assignment.doctor
        else:
            messages.warning(request, "You're not currently assigned to any doctor.")
            return redirect('doctor:dashboard')
    
    # Get patient
    patient = get_object_or_404(PatientProfile, pk=pk)
    
    # Check if this doctor has treated this patient before
    has_treated = Appointment.objects.filter(doctor=doctor_profile, patient=patient).exists()
    if not has_treated:
        messages.error(request, "You don't have permission to view this patient's details.")
        return redirect('doctor:patients')
    
    # Get patient's medical records with this doctor
    medical_records = MedicalRecord.objects.filter(
        doctor=doctor_profile,
        patient=patient
    ).order_by('-date_created')
    
    # Get patient's appointments with this doctor
    appointments = Appointment.objects.filter(
        doctor=doctor_profile,
        patient=patient
    ).order_by('-appointment_date', '-appointment_time')
    
    # Get patient's prescriptions from this doctor
    prescriptions = Prescription.objects.filter(
        doctor=doctor_profile,
        patient=patient
    ).order_by('-date_prescribed')
    
    # Patient notes (if doctor)
    if request.user.user_type == 'DOCTOR':
        if request.method == 'POST':
            note_form = PatientNoteForm(request.POST)
            if note_form.is_valid():
                note = note_form.save(commit=False)
                note.doctor = doctor_profile
                note.patient = patient
                note.save()
                messages.success(request, "Note added successfully")
                return redirect('doctor:patient_detail', pk=pk)
        else:
            note_form = PatientNoteForm()
        
        patient_notes = PatientNote.objects.filter(
            doctor=doctor_profile,
            patient=patient
        ).order_by('-created_at')
    else:
        note_form = None
        patient_notes = PatientNote.objects.filter(
            doctor=doctor_profile,
            patient=patient,
            is_private=False  # Nurses can only see non-private notes
        ).order_by('-created_at')
    
    context = {
        'patient': patient,
        'medical_records': medical_records,
        'appointments': appointments,
        'prescriptions': prescriptions,
        'patient_notes': patient_notes,
        'note_form': note_form,
        'is_doctor': request.user.user_type == 'DOCTOR',
        'is_nurse': request.user.user_type == 'NURSE',
    }
    
    return render(request, 'doctor/patient_detail.html', context)

@login_required
def schedule(request):
    """View for managing doctor's schedule"""
    if request.user.user_type != 'DOCTOR':
        messages.error(request, "Access denied. Doctor access only.")
        return redirect('accounts:home')
    
    doctor_profile = get_object_or_404(DoctorProfile, user=request.user)
    
    if request.method == 'POST':
        form = DoctorScheduleForm(request.POST)
        if form.is_valid():
            schedule = form.save(commit=False)
            schedule.doctor = doctor_profile
            
            # Check for overlapping schedules
            overlapping = DoctorSchedule.objects.filter(
                doctor=doctor_profile,
                day_of_week=schedule.day_of_week
            ).filter(
                (Q(start_time__lte=schedule.start_time) & Q(end_time__gt=schedule.start_time)) |
                (Q(start_time__lt=schedule.end_time) & Q(end_time__gte=schedule.end_time)) |
                (Q(start_time__gte=schedule.start_time) & Q(end_time__lte=schedule.end_time))
            )
            
            if overlapping.exists():
                messages.error(request, "This schedule overlaps with an existing one.")
            else:
                schedule.save()
                messages.success(request, "Schedule added successfully")
                return redirect('doctor:schedule')
    else:
        form = DoctorScheduleForm()
    
    # Get all schedules for the doctor
    schedules = DoctorSchedule.objects.filter(doctor=doctor_profile).order_by('day_of_week', 'start_time')
    
    # Get all specific date slots
    date_slots = DoctorAvailableTimeSlot.objects.filter(
        doctor=doctor_profile,
        date__gte=timezone.now().date()
    ).order_by('date', 'start_time')
    
    context = {
        'form': form,
        'schedules': schedules,
        'date_slots': date_slots,
    }
    
    return render(request, 'doctor/schedule.html', context)

@login_required
def delete_schedule(request, pk):
    """View for deleting a schedule"""
    if request.user.user_type != 'DOCTOR':
        messages.error(request, "Access denied. Doctor access only.")
        return redirect('accounts:home')
    
    doctor_profile = get_object_or_404(DoctorProfile, user=request.user)
    schedule = get_object_or_404(DoctorSchedule, pk=pk, doctor=doctor_profile)
    
    if request.method == 'POST':
        schedule.delete()
        messages.success(request, "Schedule deleted successfully")
        return redirect('doctor:schedule')
    
    return render(request, 'doctor/delete_schedule.html', {'schedule': schedule})

@login_required
def add_date_slot(request):
    """View for adding a specific date availability slot"""
    if request.user.user_type != 'DOCTOR':
        messages.error(request, "Access denied. Doctor access only.")
        return redirect('accounts:home')
    
    doctor_profile = get_object_or_404(DoctorProfile, user=request.user)
    
    if request.method == 'POST':
        form = DoctorAvailableTimeSlotForm(request.POST)
        if form.is_valid():
            slot = form.save(commit=False)
            slot.doctor = doctor_profile
            
            # Check for overlapping time slots
            overlapping = DoctorAvailableTimeSlot.objects.filter(
                doctor=doctor_profile,
                date=slot.date
            ).filter(
                (Q(start_time__lte=slot.start_time) & Q(end_time__gt=slot.start_time)) |
                (Q(start_time__lt=slot.end_time) & Q(end_time__gte=slot.end_time)) |
                (Q(start_time__gte=slot.start_time) & Q(end_time__lte=slot.end_time))
            )
            
            if overlapping.exists():
                messages.error(request, "This time slot overlaps with an existing one.")
            else:
                slot.save()
                messages.success(request, "Time slot added successfully")
                return redirect('doctor:schedule')
    else:
        form = DoctorAvailableTimeSlotForm()
    
    return render(request, 'doctor/add_date_slot.html', {'form': form})

@login_required
def delete_date_slot(request, pk):
    """View for deleting a specific date availability slot"""
    if request.user.user_type != 'DOCTOR':
        messages.error(request, "Access denied. Doctor access only.")
        return redirect('accounts:home')
    
    doctor_profile = get_object_or_404(DoctorProfile, user=request.user)
    slot = get_object_or_404(DoctorAvailableTimeSlot, pk=pk, doctor=doctor_profile)
    
    if request.method == 'POST':
        slot.delete()
        messages.success(request, "Time slot deleted successfully")
        return redirect('doctor:schedule')
    
    return render(request, 'doctor/delete_date_slot.html', {'slot': slot})

@login_required
def request_leave(request):
    """View for requesting leave/time off"""
    if request.user.user_type != 'DOCTOR':
        messages.error(request, "Access denied. Doctor access only.")
        return redirect('accounts:home')
    
    doctor_profile = get_object_or_404(DoctorProfile, user=request.user)
    
    if request.method == 'POST':
        form = DoctorLeaveForm(request.POST)
        if form.is_valid():
            leave = form.save(commit=False)
            leave.doctor = doctor_profile
            leave.status = 'PENDING'
            leave.save()
            messages.success(request, "Leave request submitted successfully")
            return redirect('doctor:leaves')
    else:
        form = DoctorLeaveForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'doctor/request_leave.html', context)

@login_required
def leaves(request):
    """View for managing doctor's leave requests"""
    if request.user.user_type != 'DOCTOR':
        messages.error(request, "Access denied. Doctor access only.")
        return redirect('accounts:home')
    
    doctor_profile = get_object_or_404(DoctorProfile, user=request.user)
    
    # Get all leave requests for the doctor
    leaves = DoctorLeave.objects.filter(doctor=doctor_profile).order_by('-start_date')
    
    context = {
        'leaves': leaves,
    }
    
    return render(request, 'doctor/leaves.html', context)

@login_required
def cancel_leave(request, pk):
    """View for cancelling a leave request"""
    if request.user.user_type != 'DOCTOR':
        messages.error(request, "Access denied. Doctor access only.")
        return redirect('accounts:home')
    
    doctor_profile = get_object_or_404(DoctorProfile, user=request.user)
    leave = get_object_or_404(DoctorLeave, pk=pk, doctor=doctor_profile)
    
    if leave.status != 'PENDING':
        messages.error(request, "Cannot cancel a leave that is not in pending status.")
        return redirect('doctor:leaves')
    
    if request.method == 'POST':
        leave.delete()
        messages.success(request, "Leave request cancelled successfully")
        return redirect('doctor:leaves')
    
    return render(request, 'doctor/cancel_leave.html', {'leave': leave})

@login_required
def tasks(request):
    """View for managing tasks"""
    if request.user.user_type not in ['DOCTOR', 'NURSE']:
        messages.error(request, "Access denied. Doctor or Nurse access only.")
        return redirect('accounts:home')
    
    if request.user.user_type == 'DOCTOR':
        doctor_profile = get_object_or_404(DoctorProfile, user=request.user)
        
        if request.method == 'POST':
            form = TaskForm(request.POST)
            if form.is_valid():
                task = form.save(commit=False)
                task.doctor = doctor_profile
                task.status = 'PENDING'
                task.save()
                messages.success(request, "Task assigned successfully")
                return redirect('doctor:tasks')
        else:
            form = TaskForm()
        
        # Get all tasks created by the doctor
        tasks = Task.objects.filter(doctor=doctor_profile).order_by('status', 'priority', 'due_date')
        
        context = {
            'is_doctor': True,
            'tasks': tasks,
            'form': form,
        }
    else:  # Nurse
        # Get all tasks assigned to the nurse
        tasks = Task.objects.filter(assigned_to=request.user).order_by('status', 'priority', 'due_date')
        
        context = {
            'is_nurse': True,
            'tasks': tasks,
        }
    
    return render(request, 'doctor/tasks.html', context)

@login_required
def task_detail(request, pk):
    """View for task details and updates"""
    if request.user.user_type not in ['DOCTOR', 'NURSE']:
        messages.error(request, "Access denied. Doctor or Nurse access only.")
        return redirect('accounts:home')
    
    # Get task and verify permission
    task = get_object_or_404(Task, pk=pk)
    
    if request.user.user_type == 'DOCTOR':
        doctor_profile = get_object_or_404(DoctorProfile, user=request.user)
        if task.doctor != doctor_profile:
            messages.error(request, "You don't have permission to view this task.")
            return redirect('doctor:tasks')
        is_doctor = True
        is_nurse = False
    else:  # Nurse
        if task.assigned_to != request.user:
            messages.error(request, "You don't have permission to view this task.")
            return redirect('doctor:tasks')
        is_doctor = False
        is_nurse = True
    
    if request.method == 'POST':
        if 'complete_task' in request.POST and is_nurse:
            task.status = 'COMPLETED'
            task.completed_at = timezone.now()
            task.save()
            messages.success(request, "Task marked as completed")
            return redirect('doctor:tasks')
        elif 'update_status' in request.POST and is_doctor:
            new_status = request.POST.get('status')
            if new_status in dict(Task.STATUS_CHOICES):
                task.status = new_status
                if new_status == 'COMPLETED':
                    task.completed_at = timezone.now()
                task.save()
                messages.success(request, "Task status updated")
                return redirect('doctor:task_detail', pk=pk)
    
    context = {
        'task': task,
        'is_doctor': is_doctor,
        'is_nurse': is_nurse,
    }
    
    return render(request, 'doctor/task_detail.html', context)

@login_required
def delete_task(request, pk):
    """View for deleting a task"""
    if request.user.user_type != 'DOCTOR':
        messages.error(request, "Access denied. Doctor access only.")
        return redirect('accounts:home')
    
    doctor_profile = get_object_or_404(DoctorProfile, user=request.user)
    task = get_object_or_404(Task, pk=pk, doctor=doctor_profile)
    
    if request.method == 'POST':
        task.delete()
        messages.success(request, "Task deleted successfully")
        return redirect('doctor:tasks')
    
    return render(request, 'doctor/delete_task.html', {'task': task})

@login_required
def manage_nurses(request):
    """View for managing nurse assignments"""
    if request.user.user_type != 'DOCTOR':
        messages.error(request, "Access denied. Doctor access only.")
        return redirect('accounts:home')
    
    doctor_profile = get_object_or_404(DoctorProfile, user=request.user)
    
    if request.method == 'POST':
        form = NurseAssignmentForm(request.POST)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.doctor = doctor_profile
            assignment.save()
            messages.success(request, "Nurse assigned successfully")
            return redirect('doctor:manage_nurses')
    else:
        form = NurseAssignmentForm()
    
    # Get all nurse assignments for the doctor
    assignments = NurseAssignment.objects.filter(doctor=doctor_profile).order_by('-is_active', '-start_date')
    
    context = {
        'form': form,
        'assignments': assignments,
    }
    
    return render(request, 'doctor/manage_nurses.html', context)

@login_required
def remove_nurse(request, pk):
    """View for ending a nurse assignment"""
    if request.user.user_type != 'DOCTOR':
        messages.error(request, "Access denied. Doctor access only.")
        return redirect('accounts:home')
    
    doctor_profile = get_object_or_404(DoctorProfile, user=request.user)
    assignment = get_object_or_404(NurseAssignment, pk=pk, doctor=doctor_profile)
    
    if request.method == 'POST':
        assignment.is_active = False
        assignment.end_date = timezone.now().date()
        assignment.save()
        messages.success(request, "Nurse assignment ended successfully")
        return redirect('doctor:manage_nurses')
    
    return render(request, 'doctor/remove_nurse.html', {'assignment': assignment})

@login_required
def create_referral(request, patient_id):
    """View for creating a referral for a patient"""
    if request.user.user_type != 'DOCTOR':
        messages.error(request, "Access denied. Doctor access only.")
        return redirect('accounts:home')
    
    doctor_profile = get_object_or_404(DoctorProfile, user=request.user)
    patient = get_object_or_404(PatientProfile, pk=patient_id)
    
    # Check if this doctor has treated this patient before
    has_treated = Appointment.objects.filter(doctor=doctor_profile, patient=patient).exists()
    if not has_treated:
        messages.error(request, "You don't have permission to create a referral for this patient.")
        return redirect('doctor:patients')
    
    if request.method == 'POST':
        form = ReferralForm(request.POST, referring_doctor=doctor_profile)
        if form.is_valid():
            referral = form.save(commit=False)
            referral.patient = patient
            referral.referring_doctor = doctor_profile
            referral.save()
            messages.success(request, "Referral created successfully")
            return redirect('doctor:patient_detail', pk=patient_id)
    else:
        form = ReferralForm(referring_doctor=doctor_profile)
    
    context = {
        'form': form,
        'patient': patient,
    }
    
    return render(request, 'doctor/create_referral.html', context)

@login_required
def referrals(request):
    """View for managing referrals"""
    if request.user.user_type != 'DOCTOR':
        messages.error(request, "Access denied. Doctor access only.")
        return redirect('accounts:home')
    
    doctor_profile = get_object_or_404(DoctorProfile, user=request.user)
    
    # Get referrals made by this doctor
    outgoing_referrals = Referral.objects.filter(referring_doctor=doctor_profile).order_by('-referral_date')
    
    # Get referrals made to this doctor
    incoming_referrals = Referral.objects.filter(referred_to_doctor=doctor_profile).order_by('-referral_date')
    
    context = {
        'outgoing_referrals': outgoing_referrals,
        'incoming_referrals': incoming_referrals,
    }
    
    return render(request, 'doctor/referrals.html', context)

@login_required
def referral_detail(request, pk):
    """View for referral details and actions"""
    if request.user.user_type != 'DOCTOR':
        messages.error(request, "Access denied. Doctor access only.")
        return redirect('accounts:home')
    
    doctor_profile = get_object_or_404(DoctorProfile, user=request.user)
    referral = get_object_or_404(
        Referral.objects.filter(
            Q(referring_doctor=doctor_profile) | Q(referred_to_doctor=doctor_profile),
            pk=pk
        )
    )
    
    # Determine if this is an incoming or outgoing referral
    is_incoming = (referral.referred_to_doctor == doctor_profile)
    
    if request.method == 'POST':
        if is_incoming:
            action = request.POST.get('action')
            if action == 'accept':
                referral.status = 'ACCEPTED'
                referral.save()
                messages.success(request, "Referral accepted successfully")
                return redirect('doctor:referral_detail', pk=pk)
            elif action == 'decline':
                referral.status = 'DECLINED'
                referral.save()
                messages.success(request, "Referral declined")
                return redirect('doctor:referral_detail', pk=pk)
            elif action == 'complete':
                referral.status = 'COMPLETED'
                referral.completion_date = timezone.now().date()
                referral.save()
                messages.success(request, "Referral marked as completed")
                return redirect('doctor:referral_detail', pk=pk)
    
    context = {
        'referral': referral,
        'is_incoming': is_incoming,
    }
    
    return render(request, 'doctor/referral_detail.html', context)

@login_required
def generate_bill(request, prescription_id):
    """View for generating a bill for a prescription"""
    if request.user.user_type != 'DOCTOR':
        messages.error(request, "Access denied. Doctor access only.")
        return redirect('accounts:home')
    
    doctor_profile = get_object_or_404(DoctorProfile, user=request.user)
    prescription = get_object_or_404(Prescription, pk=prescription_id, doctor=doctor_profile)
    
    # Check if bill already exists
    if Bill.objects.filter(prescription=prescription).exists():
        messages.error(request, "A bill already exists for this prescription.")
        return redirect('doctor:prescription_detail', pk=prescription_id)
    
    if request.method == 'POST':
        amount = request.POST.get('amount')
        tax = request.POST.get('tax', 0)
        discount = request.POST.get('discount', 0)
        description = request.POST.get('description', '')
        due_date = request.POST.get('due_date')
        
        try:
            amount = float(amount)
            tax = float(tax)
            discount = float(discount)
            
            # Calculate total
            total_amount = amount + tax - discount
            
            # Create bill
            bill = Bill.objects.create(
                patient=prescription.patient,
                prescription=prescription,
                amount=amount,
                tax=tax,
                discount=discount,
                total_amount=total_amount,
                status='PENDING',
                due_date=due_date,
                description=description
            )
            
            messages.success(request, "Bill generated successfully")
            return redirect('doctor:prescription_detail', pk=prescription_id)
            
        except (ValueError, TypeError):
            messages.error(request, "Invalid amount values.")
    
    # Get prescription items for reference
    prescription_items = PrescriptionItem.objects.filter(prescription=prescription)
    
    # Calculate suggested bill amount based on medicine prices
    suggested_amount = sum(item.medicine.unit_price * item.quantity for item in prescription_items)
    
    # Add consultation fee
    suggested_amount += doctor_profile.consultation_fee
    
    context = {
        'prescription': prescription,
        'prescription_items': prescription_items,
        'suggested_amount': suggested_amount,
        'consultation_fee': doctor_profile.consultation_fee,
    }
    
    return render(request, 'doctor/generate_bill.html', context)

@login_required
def medicine_inventory(request):
    """View for checking medicine inventory"""
    if request.user.user_type not in ['DOCTOR', 'NURSE']:
        messages.error(request, "Access denied. Doctor or Nurse access only.")
        return redirect('accounts:home')
    
    # Search filter
    search = request.GET.get('search', '')
    
    # Get all medicines
    medicines = Medicine.objects.all().order_by('name')
    
    # Apply search filter if provided
    if search:
        medicines = medicines.filter(name__icontains=search)
    
    # Pagination
    paginator = Paginator(medicines, 20)  # Show 20 medicines per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'medicines': page_obj,
        'search': search,
        'is_doctor': request.user.user_type == 'DOCTOR',
        'is_nurse': request.user.user_type == 'NURSE',
    }
    
    return render(request, 'doctor/medicine_inventory.html', context)

@login_required
def delete_prescription_item(request, pk):
    """View for deleting a medicine item from a prescription"""
    if request.user.user_type != 'DOCTOR':
        messages.error(request, "Access denied. Doctor access only.")
        return redirect('accounts:home')
    
    item = get_object_or_404(PrescriptionItem, pk=pk)
    prescription = item.prescription
    
    if prescription.doctor.user != request.user:
        messages.error(request, "You don't have permission to modify this prescription.")
        return redirect('doctor:prescriptions')
    
    if request.method == 'POST':
        prescription_id = prescription.id
        item.delete()
        messages.success(request, "Medicine removed from prescription")
        return redirect('doctor:edit_prescription', pk=prescription_id)
    
    return render(request, 'doctor/delete_prescription_item.html', {'item': item})