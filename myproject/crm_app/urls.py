from django.urls import path, include
from .views import *
from rest_framework import routers


router = routers.SimpleRouter()


urlpatterns = [
    path('', include(router.urls)),

    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('login_admin/', CustomAdminLoginView.as_view(), name='login_admin'),
    path('logout/', LogoutView.as_view(), name='logout'),

    path('records/', RecordsListApiView.as_view() ,name='appointment_list'),
    path('patient_create/', PatientCreateApView.as_view(), name='patient_create'),
    path('doctor_create/', DoctorCreateApiView.as_view(), name='doctor_create'),
    path('doctor_create/save/', DoctorSaveApiView.as_view(), name='doctor_save'),  
    path('records/<int:pk>/', RecordsDetailApiView.as_view(), name = 'info_patient'),
    path('records/<int:pk>/history/', PatientAppointmentReportView.as_view(), name='history_patient'),
    path('records/<int:pk>/history/waiting/', PatientWaitingAppointmentsAPIView.as_view(), name='status_waiting'),
    path('records/<int:pk>/history/payment/', PatientPaymentReportView.as_view()),
    path('records/<int:pk>/history/payment/info', InfoPatientApiView.as_view(), name='info_patient'),
    path('doctors/', DoctorsApiView.as_view(), name = 'doctor_list'),
    path('doctors/<int:pk>/', DoctorAppointmentsApiView.as_view(), name = 'detailed_report'),
    path('doctors/<int:pk>/bonus/', DoctorReportListAPIView.as_view(), name='doctor_bonus'),
    path('summary_clinic/', SummaryReportClinicAPIView.as_view(), name='summary_clinic'),
    path('doctors/schedule/', DoctorScheduleApiView.as_view(), name='doctor_schedule'),
    path('price_list/', PriceListApiView.as_view(), name='price_list')

]
