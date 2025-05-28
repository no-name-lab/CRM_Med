from rest_framework import viewsets, permissions
from .models import DoctorSchedule, Appointment
from .serializers import DoctorScheduleSerializer, AppointmentSerializer


class DoctorScheduleViewSet(viewsets.ModelViewSet):
    queryset = DoctorSchedule.objects.all()
    serializer_class = DoctorScheduleSerializer
    # permission_classes = [permissions.IsAuthenticated]


class AppointmentViewSet(viewsets.ModelViewSet):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    # permission_classes = [permissions.IsAuthenticated]
