from rest_framework import serializers
from .models import *


class CustomUserSerializers(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = '__all__'


class DepartmentSerializers(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = '__all__'


class ServiceSerializers(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = '__all__'


class PatientSerializers(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = '__all__'


class DoctorSerializers(serializers.ModelSerializer):
    class Meta:
        model = Doctor
        fields = '__all__'


class DoctorScheduleSerializers(serializers.ModelSerializer):
    class Meta:
        model = DoctorSchedule
        fields = '__all__'


class AppointmentSerializers(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = '__all__'