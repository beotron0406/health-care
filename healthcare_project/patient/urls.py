# patient/urls.py

from django.urls import path
from . import views

app_name = 'patient'

urlpatterns = [
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Appointments
    path('appointments/', views.appointments, name='appointments'),
    path('appointments/<int:pk>/', views.appointment_detail, name='appointment_detail'),
    path('appointments/<int:pk>/cancel/', views.cancel_appointment, name='cancel_appointment'),
    
    # Medical Records
    path('medical-records/', views.medical_records, name='medical_records'),
    path('medical-records/<int:pk>/', views.medical_record_detail, name='medical_record_detail'),
    
    # Prescriptions
    path('prescriptions/', views.prescriptions, name='prescriptions'),
    path('prescriptions/<int:pk>/', views.prescription_detail, name='prescription_detail'),
    
    # Bills
    path('bills/', views.bills, name='bills'),
    path('bills/<int:pk>/', views.bill_detail, name='bill_detail'),
    
    # Insurance
    path('insurance/', views.insurance, name='insurance'),
    path('insurance/claim/<int:bill_id>/', views.submit_insurance_claim, name='submit_insurance_claim'),
    
    # Doctor Search
    path('doctors/', views.search_doctors, name='search_doctors'),
]