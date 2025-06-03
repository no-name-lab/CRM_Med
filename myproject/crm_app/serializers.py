from django.contrib.auth import authenticate
from rest_framework import serializers
from reception.models import  Doctor, Patient, UserProfile, Department, Service, CustomerRecord, HistoryRecord, Reception
from rest_framework.serializers import Serializer
from rest_framework_simplejwt.tokens import RefreshToken
from .models import *
from django.db.models import F, ExpressionWrapper, FloatField, Sum, Count, Q
from decimal import Decimal


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = UserProfile
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'password', 'role']

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = UserProfile.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(**data)
        if user and user.is_active:
            return user
        raise serializers.ValidationError("Неверные учетные данные")

    def to_representation(self, instance):
        refresh = RefreshToken.for_user(instance)
        return {
            'user': {
                'first_name': instance.first_name,
                'last_name': instance.last_name,
                'email': instance.email,
                'role': instance.role,

            },
            'access': str(refresh.access_token),
            'refresh': str(refresh),
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


class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = ['full_name']


class CustomUserSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['first_name', 'last_name']


class DoctorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Doctor
        fields = ['first_name', 'last_name']


class DepartmentSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['id', 'name']


class ServiceSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ['name', 'price']


class ReceptionSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reception
        fields = ['desk_name']


#Записи на прием
class AppointmentAdminSerializer(serializers.ModelSerializer):
    created_date = serializers.DateTimeField(format='%d-%m-%Y')
    time = serializers.TimeField(format='%H:%M')
    patient = PatientSerializer()
    doctor = DoctorSerializer()

    class Meta:
        model = CustomerRecord
        fields = ['id', 'created_date', 'time', 'patient', 'doctor', 'payment_type', 'price']


#Добавление пациента
class PatientAdminCreateSerializer(serializers.ModelSerializer):
    date_birth = serializers.DateField(format='%d-%m_%Y')

    class Meta:
        model = Patient
        fields = ['id', 'full_name', 'date_birth', 'gender', 'phone_number']


class AppointmentPatientSerializer(serializers.ModelSerializer):
    patient = PatientAdminCreateSerializer()
    start_at = serializers.TimeField(format='%H:%M', input_formats=['%H:%M'])
    end_at = serializers.TimeField(format='%H:%M', input_formats=['%H:%M'])

    class Meta:
        model = CustomerRecord
        fields = ['id', 'patient','doctor', 'reception', 'department', 'service', 'status', 'start_at', 'end_at', 'price']


#ИНФО О ПАЦИЕНТЕ
class InfoAppointmentSerializer(serializers.ModelSerializer):
    reception = ReceptionSimpleSerializer()
    doctor = DoctorSerializer()
    department = DepartmentSimpleSerializer()
    service = ServiceSimpleSerializer()

    class Meta:
        model = CustomerRecord
        fields = ['reception', 'doctor', 'start_at', 'end_at', 'status', 'department', 'service']


#История записей
class AppointmentHistorySerializer(serializers.ModelSerializer):
    reception = ReceptionSimpleSerializer()
    created_date = serializers.DateTimeField(format='%d-%m-%Y')
    time = serializers.TimeField(format='%H:%M')
    doctor = DoctorSerializer()
    department = DepartmentSimpleSerializer()
    service = ServiceSimpleSerializer()
    delete_url = serializers.SerializerMethodField()

    total_appointments = serializers.SerializerMethodField()
    status_counts = serializers.SerializerMethodField()

    class Meta:
        model = CustomerRecord
        fields = ['id', 'reception', 'department', 'doctor', 'service', 'created_date', 'time', 'status',
                  'delete_url', 'total_appointments', 'status_counts']

    def get_delete_url(self, obj):
        return f"/appointment/admin/{obj.id}/history/{obj.id}/delete/"

    def get_total_appointments(self, obj):
        if obj.patient:
            return CustomerRecord.objects.filter(patient=obj.patient).count()
        return 0

    def get_status_counts(self, obj):
        if not obj.patient:
            return {}

        qs = CustomerRecord.objects.filter(patient=obj.patient)
        return qs.aggregate(
            waiting=Count('id', filter=Q(status='в ожидании')),
            reserved=Count('id', filter=Q(status='Предзапись')),
            cancelled=Count('id', filter=Q(status='Отменено')),
        )


#История приемов
class AppointmentWaitingHistorySerializer(serializers.ModelSerializer):
    reception = ReceptionSimpleSerializer()
    created_date = serializers.DateTimeField(format='%d-%m-%Y')
    time = serializers.TimeField(format='%H:%M')
    doctor = DoctorSerializer()
    department = DepartmentSimpleSerializer()
    service = ServiceSimpleSerializer()

    total_appointments = serializers.SerializerMethodField()
    status_counts = serializers.SerializerMethodField()

    class Meta:
        model = CustomerRecord
        fields = ['id', 'reception', 'department', 'doctor', 'service', 'created_date', 'time', 'status', 'total_appointments', 'status_counts']


    def get_total_appointments(self, obj):
        if obj.patient:
            return CustomerRecord.objects.filter(patient=obj.patient).count()
        return 0

    def get_status_counts(self, obj):
        if not obj.patient:
            return {}

        qs = CustomerRecord.objects.filter(patient=obj.patient)
        return qs.aggregate(
            waiting=Count('id', filter=Q(status='в ожидании')),
            reserved=Count('id', filter=Q(status='Предзапись')),
            cancelled=Count('id', filter=Q(status='Отменено')),
        )


#Оплата
class PatientPaymentReportSerializer(serializers.ModelSerializer):
    department = DepartmentSimpleSerializer()
    service = ServiceSimpleSerializer()
    created_date = serializers.DateTimeField(format='%d-%m-%Y')

    total_paid = serializers.SerializerMethodField()
    payment_method_sums = serializers.SerializerMethodField()

    class Meta:
        model = CustomerRecord
        fields = ['department', 'doctor', 'service', 'created_date', 'time', 'payment_type', 'price', 'total_paid', 'payment_method_sums']

    def get_total_paid(self, obj):
        if obj.patient:
            return CustomerRecord.objects.filter(patient=obj.patient).aggregate(
                total=Sum('price')
            )['total'] or 0
        return 0

    def get_payment_method_sums(self, obj):
        if not obj.patient:
            return {}

        qs = CustomerRecord.objects.filter(patient=obj.patient)
        data = qs.values('payment_type').annotate(total=Sum('price'))
        return {item['payment_type']: item['total'] for item in data}


#Данные пациента
class InformationPatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = ['full_name', 'phone_number', 'gender']


#Список врачей
class DoctorsSerializer(serializers.ModelSerializer):
    department = DepartmentSimpleSerializer()

    class Meta:
        model = Doctor
        fields = ['id', 'first_name', 'last_name', 'cabinet', 'department', 'phone_number']


#Добавление врача
class DoctorCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Doctor
        fields = ['id', 'first_name', 'last_name', 'image', 'department', 'job_title', 'phone_number', 'email']


#Сохранение врача
class DoctorSaveSerializer(serializers.ModelSerializer):
    class Meta:
        model = Doctor
        fields = ['id', 'image', 'first_name', 'last_name', 'email', 'phone_number', 'department', 'job_title', 'bonus']


#Подробный отчет
class DoctorAppointmentSerializer(serializers.ModelSerializer):
    patient = PatientSerializer()
    service = ServiceSimpleSerializer()
    created_date = serializers.DateTimeField(format='%d-%m-%Y')
    discount_price = serializers.SerializerMethodField()
    bonus = serializers.SerializerMethodField()

    class Meta:
        model = CustomerRecord
        fields = ['id', 'created_date', 'patient', 'service', 'payment_type', 'price', 'discount_price', 'bonus']

    def get_discount_price(self, obj):
        price = obj.price or 0
        discount = obj.discount or 0
        return round(price - (price * discount / 100), 2)

    def get_bonus(self, obj):
        if obj.doctor and hasattr(obj.doctor, 'bonus'):
            return obj.doctor.bonus
        return 0


class DoctorReportSerializer(serializers.ModelSerializer):
    doctor_customer = DoctorAppointmentSerializer(read_only=True, many=True)

    total_price = serializers.SerializerMethodField()
    total_discounted_price = serializers.SerializerMethodField()
    total_bonus = serializers.SerializerMethodField()
    total_appointments = serializers.SerializerMethodField()
    payment_method_sums = serializers.SerializerMethodField()

    class Meta:
        model = Doctor
        fields = ['doctor_customer', 'total_price', 'total_discounted_price', 'total_bonus', 'total_appointments', 'payment_method_sums']

    def get_total_price(self, obj):
        return obj.total_price()

    def get_total_discounted_price(self, obj):
        return obj.total_discounted_price()

    def get_total_bonus(self, obj):
        return obj.total_bonus()

    def get_total_appointments(self, obj):
        return obj.total_appointments()

    def get_payment_method_sums(self, obj):
        return obj.payment_method_sums()


#по врачам (процент врачам)
class DoctorDailyBonusSerializer(serializers.ModelSerializer):
    doctor_name = serializers.SerializerMethodField()
    cabinet = serializers.IntegerField(source='doctor.cabinet')
    bonus = serializers.SerializerMethodField()

    class Meta:
        model = CustomerRecord
        fields = ['id', 'doctor_name', 'cabinet', 'created_date', 'bonus']

    def get_doctor_name(self, obj):
        return f"{obj.doctor.user.last_name} {obj.doctor.user.first_name}"

    def get_bonus(self, obj):
        bonus_percent = Decimal(getattr(obj.doctor, 'bonus', 0))
        price = Decimal(obj.price or 0)
        discount = Decimal(obj.discount or 0)
        discounted_price = price - (price * discount / Decimal(100))
        return round(discounted_price * bonus_percent / Decimal(100), 2)


# Управление календарем
class DoctorSchedulesSerializer(serializers.ModelSerializer):
    department = DepartmentSimpleSerializer()

    class Meta:
        model = Doctor
        fields = ['first_name', 'last_name', 'image', 'speciality', 'department']


class AppointmentScheduleSerializer(serializers.ModelSerializer):
    start_at = serializers.TimeField(format='%H:%M')
    end_at = serializers.TimeField(format='%H:%M')
    doctor = DoctorSchedulesSerializer()

    class Meta:
        model = CustomerRecord
        fields = ['id', 'doctor', 'start_at', 'end_at', 'status']


#Прайс лист
class PriceListSerializer(serializers.ModelSerializer):
    services = ServiceSimpleSerializer(read_only=True, many=True)

    class Meta:
        model = Department
        fields = ['id', 'name', 'services']