from rest_framework import serializers
from .models import DoctorSchedule, Appointment


class DoctorScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoctorSchedule
        fields = '__all__'


class AppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = '__all__'

    def validate(self, data):
        doctor = data['doctor']
        date = data['date']
        time = data['time']
        if Appointment.objects.filter(doctor=doctor, date=date, time=time).exists():
            raise serializers.ValidationError("На это время уже есть запись к врачу.")
        return data