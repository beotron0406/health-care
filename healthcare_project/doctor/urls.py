# doctor/urls.py

from django.urls import path
from . import views

app_name = 'doctor'

urlpatterns = [
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Appointments
    path('appointments/', views.appointments, name='appointments'),
    path('appointments/<int:pk>/', views.appointment_detail, name='appointment_detail'),
    path('appointments/<int:appointment_id>/create-medical-record/', views.create_medical_record, name='create_medical_record'),
    
    # Medical Records
    path('medical-records/', views.medical_records, name='medical_records'),
    path('medical-records/<int:pk>/', views.medical_record_detail, name='medical_record_detail'),
    path('medical-records/<int:pk>/edit/', views.edit_medical_record, name='edit_medical_record'),
    
    # Prescriptions
    path('prescriptions/', views.prescriptions, name='prescriptions'),
    path('prescriptions/create/<int:record_id>/', views.create_prescription, name='create_prescription_from_record'),
    path('prescriptions/create-for-patient/<int:patient_id>/', views.create_prescription, name='create_prescription_for_patient'),
    path('prescriptions/<int:pk>/', views.prescription_detail, name='prescription_detail'),
    path('prescriptions/<int:pk>/edit/', views.edit_prescription, name='edit_prescription'),
    path('prescriptions/<int:prescription_id>/generate-bill/', views.generate_bill, name='generate_bill'),
    path('prescription-items/<int:pk>/delete/', views.delete_prescription_item, name='delete_prescription_item'),
    
    # Patients
    path('patients/', views.patients, name='patients'),
    path('patients/<int:pk>/', views.patient_detail, name='patient_detail'),
    path('patients/<int:patient_id>/create-referral/', views.create_referral, name='create_referral'),
    
    # Schedule
    path('schedule/', views.schedule, name='schedule'),
    path('schedule/<int:pk>/delete/', views.delete_schedule, name='delete_schedule'),
    path('schedule/add-date-slot/', views.add_date_slot, name='add_date_slot'),
    path('schedule/date-slot/<int:pk>/delete/', views.delete_date_slot, name='delete_date_slot'),
    
    # Leave
    path('leaves/', views.leaves, name='leaves'),
    path('leaves/request/', views.request_leave, name='request_leave'),
    path('leaves/<int:pk>/cancel/', views.cancel_leave, name='cancel_leave'),
    
    # Tasks
    path('tasks/', views.tasks, name='tasks'),
    path('tasks/<int:pk>/', views.task_detail, name='task_detail'),
    path('tasks/<int:pk>/delete/', views.delete_task, name='delete_task'),
    
    # Nurse Management
    path('nurses/', views.manage_nurses, name='manage_nurses'),
    path('nurses/<int:pk>/remove/', views.remove_nurse, name='remove_nurse'),
    
    # Referrals
    path('referrals/', views.referrals, name='referrals'),
    path('referrals/<int:pk>/', views.referral_detail, name='referral_detail'),
    
    # Medicine
    path('medicines/', views.medicine_inventory, name='medicine_inventory'),
]