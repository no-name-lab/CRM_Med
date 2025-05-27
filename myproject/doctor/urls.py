from django.urls import path, include
from .views import *
from rest_framework import routers

router = routers.SimpleRouter()
router.register(r'schedule', DoctorScheduleViewSet, basename='schedule-list')
router.register(r'appointment', AppointmentViewSet, basename='appointment-list')


urlpatterns = [
    path('', include(router.urls)),
]