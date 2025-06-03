from .models import *
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = '__all__'


class UserProfileRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['first_name', 'last_name', 'email', 'phone_number','password']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = UserProfile.objects.create_user(**validated_data)
        return user

    def to_representation(self, instance):
        refresh = RefreshToken.for_user(instance)
        return {
            'user': {
                'email': instance.email,
            },
            'access': str(refresh.access_token),
            'refresh': str(refresh)
        }


class ReceptionRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = Reception
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'password']

    def create(self, validated_data):
        validated_data['role'] = 'reception'
        user = Reception.objects.create_user(**validated_data)
        return user

    def to_representation(self, instance):
        refresh = RefreshToken.for_user(instance)
        return {
            'user': {
                'email': instance.email,
                'role': instance.role,
            },
            'access': str(refresh.access_token),
            'refresh': str(refresh)
        }


class DoctorRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = Doctor
        fields = ['first_name', 'last_name', 'cabinet', 'speciality', 'medical_license', 'email', 'phone_number',
                  'password']

    def create(self, validated_data):
        validated_data['role'] = 'doctor'
        user = Doctor.objects.create_user(**validated_data)
        return user

    def to_representation(self, instance):
        refresh = RefreshToken.for_user(instance)
        return {
            'user': {
                'email': instance.email,
                'role': instance.role,
            },
            'access': str(refresh.access_token),
            'refresh': str(refresh)
        }


class LoginSerializers(serializers.Serializer):
    email = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(**data)
        if user and user.is_active:
            return {
                'user': user
            }
        raise serializers.ValidationError("Неверные учетные данные")

    def to_representation(self, validated_data):
        user = validated_data['user']
        refresh = RefreshToken.for_user(user)
        return {
            'user': {
                'email': user.email,
                'role': user.role,
            },
            'access': str(refresh.access_token),
            'refresh': str(refresh)
        }


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    def validate(self, data):
        self.token = data['refresh']
        return data

    def save(self, **kwargs):
        try:
            token = RefreshToken(self.token)
            token.blacklist()
        except Exception as e:
            raise serializers.ValidationError({'detail': 'Недействительный или уже отозванный токен'})


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['name']


class DoctorCabinetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Doctor
        fields = ['first_name', 'cabinet']


class ReceptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reception
        fields = ['first_name']


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ['name']


class ServiceDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ['name', 'price']


class PatientSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = ['full_name']


class DoctorSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Doctor
        fields = ['first_name']


class CustomerRecordListSerializer(serializers.ModelSerializer):
    department = DepartmentSerializer(read_only=True)
    patient = PatientSimpleSerializer(read_only=True)
    doctor = DoctorSimpleSerializer(read_only=True)
    created_date = serializers.DateTimeField(format='%d %B %Y')

    class Meta:
        model = CustomerRecord
        fields = ['department', 'patient', 'created_date', 'doctor', 'payment_type', 'price']


class PatientCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = ['full_name', 'date_birth', 'gender', 'phone_number']


class CustomerRecordRetrieveSerializer(serializers.ModelSerializer):
    patient = PatientSimpleSerializer(read_only=True)
    doctor = DoctorSimpleSerializer(read_only=True)
    service = ServiceSerializer(read_only=True)

    class Meta:
        model = CustomerRecord
        fields = ['patient', 'doctor', 'service', 'price', 'change', 'payment_type']


class CustomerRecordCreateSerializer(serializers.ModelSerializer):
    patient = PatientCreateSerializer()

    class Meta:
        model = CustomerRecord
        fields = ['patient', 'department', 'doctor', 'service', 'reception', 'status', 'time', 'price']

    def create(self, validated_data):
        patient_data = validated_data.pop('patient')
        patient = Patient.objects.create(**patient_data)
        customer_record = CustomerRecord.objects.create(patient=patient, **validated_data)
        return customer_record


class DoctorListSerializer(serializers.ModelSerializer):
    department = DepartmentSerializer(read_only=True)

    class Meta:
        model = Doctor
        fields = ['speciality', 'cabinet', 'department', 'phone_number']


class AboutPatientRecordSerializer(serializers.ModelSerializer):
    doctor = DoctorSimpleSerializer(read_only=True)
    service = ServiceSerializer(read_only=True)
    reception = ReceptionSerializer(read_only=True)
    department = DepartmentSerializer(read_only=True)

    class Meta:
        model = CustomerRecord
        fields = ['reception', 'department', 'doctor', 'service', 'time', 'status']


class AboutPatientHistoryRecordSerializer(serializers.ModelSerializer):
    department = DepartmentSerializer(read_only=True)
    doctor = DoctorSimpleSerializer(read_only=True)
    service = ServiceSerializer(read_only=True)
    reception = ReceptionSerializer(read_only=True)
    created_date = serializers.DateTimeField(format='%d %m %Y')

    class Meta:
        model = CustomerRecord
        fields = ['id', 'reception', 'department', 'doctor', 'service', 'records', 'created_date']


class AboutPatientHistorySerializer(serializers.ModelSerializer):
    department = DepartmentSerializer(read_only=True)
    doctor = DoctorSimpleSerializer(read_only=True)
    service = ServiceSerializer(read_only=True)
    reception = ReceptionSerializer(read_only=True)
    total_records = serializers.SerializerMethodField()
    was_on_reception = serializers.SerializerMethodField()

    class Meta:
        model = CustomerRecord
        fields = ['reception', 'department', 'doctor', 'service', 'records', 'total_records', 'was_on_reception']

    def get_total_records(self, obj):
        return obj.get_total_records()

    def get_was_on_reception(self, obj):
        return obj.get_was_on_reception()


class PaymentSerializer(serializers.ModelSerializer):
    department = DepartmentSerializer(read_only=True)
    doctor = DoctorSimpleSerializer(read_only=True)
    service = ServiceSerializer(read_only=True)
    created_date = serializers.DateTimeField(format='%d %B %Y')

    class Meta:
        model = CustomerRecord
        fields = ['department', 'doctor', 'service', 'payment_type', 'price', 'created_date']


class InfoPatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = ['full_name', 'phone_number', 'gender']


class PriceListSerializer(serializers.ModelSerializer):
    department = DepartmentSerializer(read_only=True)

    class Meta:
        model = Service
        fields = ['department']


class PriceDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ['name', 'price']


class DoctorBonusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Doctor
        fields = ['bonus']


class DetailedReportSerializer(serializers.ModelSerializer):
    bonus = serializers.SerializerMethodField()
    patient = PatientSimpleSerializer(read_only=True)
    service = ServiceSerializer(read_only=True)

    class Meta:
        model = CustomerRecord
        fields = ['id', 'created_date', 'doctor', 'department', 'patient', 'service', 'payment_type', 'price',
                  'discount', 'bonus']

    def get_bonus(self, obj):
        return obj.doctor.bonus if obj.doctor else None


class DoctorReportSerializers(serializers.ModelSerializer):
    doctor = DoctorSimpleSerializer(read_only=True)

    class Meta:
        model = CustomerRecord
        fields = ['doctor', 'id', 'created_date', 'price']


class SummaryReportSerializer(serializers.Serializer):
    total_cash = serializers.IntegerField()
    total_card = serializers.IntegerField()
    total_price = serializers.IntegerField()
    total_to_doctors = serializers.IntegerField()


class DoctorCalendarSerializer(serializers.ModelSerializer):
    class Meta:
        model = Doctor
        fields = ['speciality']


class CalendarSerializer(serializers.ModelSerializer):
    speciality = DoctorCalendarSerializer(read_only=True)
    department = DepartmentSerializer(read_only=True)
    doctor = DoctorSimpleSerializer(read_only=True)
    service = ServiceSerializer(read_only=True)

    class Meta:
        model = CustomerRecord
        fields = ['doctor', 'department', 'created_date', 'time', 'service', 'status', 'speciality']




