from django.urls import path, include
from .views import *
from rest_framework import routers

router = routers.SimpleRouter()
router.register(r'user', CustomUserViewSet, basename='user-list')
router.register(r'department', DepartmentViewSet, basename='department-list')
router.register(r'service', ServiceViewSet, basename='service-list')
router.register(r'patient', PatientViewSet, basename='patient-list')
router.register(r'doctor', DoctorViewSet, basename='doctor-list')
router.register(r'schedule', DoctorScheduleViewSet, basename='schedule-list')
router.register(r'appointment', AppointmentViewSet, basename='appointment-list')


urlpatterns = [
    path('', include(router.urls)),
]