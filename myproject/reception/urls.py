from .views import *
from django.urls import path, include
from rest_framework.routers import DefaultRouter
router = DefaultRouter()
router.register(r'doctor', DoctorViewSet, basename='doctor')
router.register(r'calendar', CalendarViewSet, basename='calendar')
urlpatterns = [
    path('customer_record/', CustomerRecordListAPIView.as_view(), name='customer_record_list'),
    path('customer_record/create', CustomerRecordCreateAPIView.as_view(), name='customer_record_create'),
    path('customer_record/<int:pk>/', CustomerRecordRetrieveAPIView.as_view(),
         name='customer_record_detail'),
    path('records/<int:pk>/', CustomerRecordRetrieveUpdateDestroyAPIView.as_view(), name='records_update'),

    path('', include(router.urls)),
    path('about_patient/', AboutPatientRecordListAPIView.as_view(), name='about_patient'),
    path('about_patient/<int:pk>/', AboutPatientRecordListUpdateAPIView.as_view(), name='about_patient_update'),

    path('history/<int:patient_id>/records/', AboutPatientHistoryRecordListAPIView.as_view(), name='Patient_history'),

    path('patient/<int:patient_id>/visited-records/', PatientRecordListAPIView.as_view(), name='patient-visited-records'),


    path('payment/<int:patient_id>/patient/', PaymentListAPIView.as_view(), name='payment'),

    path('info_patient/', InfoPatientListAPIView.as_view(), name='info_patient'),

    path('price_list/', PriceListAPIView.as_view(), name='price'),
    path('price_list/<int:pk>/', PriceDetailAPIView.as_view(), name='price_detail'),

    path('detailed_record/', DetailedReportListAPIView.as_view(), name='detailed_record'),
    path('report_doctor/', DoctorReportListAPIView.as_view(), name='doctor_record'),
    path('summary_report/', SummaryReportAPIView.as_view(), name='doctor_record'),

    path('reception_register/', ReceptionRegisterView.as_view(), name='register_reception'),
    path('doctor_register/', DoctorRegisterView.as_view(), name='register_doctor'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),

]