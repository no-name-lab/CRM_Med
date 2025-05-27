from rest_framework import serializers
from .models import *


class CustomUserSerializers(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'password', 'role']


class DepartmentSerializers(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['name']


class ServiceSerializers(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ['name', 'department', 'price']


class PatientSerializers(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = ['first_name', 'last_name', 'date_birth', 'gender', 'phone_number']


class DoctorSerializers(serializers.ModelSerializer):
    class Meta:
        model = Doctor
        fields = ['user', 'speciality', 'medical_license', 'bonus', 'image', 'department', 'cabinet']


class DoctorScheduleSerializers(serializers.ModelSerializer):
    class Meta:
        model = DoctorSchedule
        fields = ['doctor', 'date', 'start_time', 'end_time', 'is_available']


class AppointmentSerializers(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = '__all__'