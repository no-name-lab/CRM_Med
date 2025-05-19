from django.contrib.auth import authenticate
from rest_framework import serializers
from doctor.models import  Doctor, Patient, CustomUser, Appointment, Department, Service, DoctorSchedule
from rest_framework.serializers import Serializer
from rest_framework_simplejwt.tokens import RefreshToken
from .models import *
from django.db.models import F, ExpressionWrapper, FloatField, Sum, Count, Q
from decimal import Decimal

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'password', 'role' ]
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
            user = CustomUser.objects.create_user(**validated_data)
            return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
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
                'phone_number': instance.phone_number,
                'role': instance.role,

            },
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }


class EmptySerializer(Serializer):
    pass


class PatientSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = ['first_name', 'last_name']


class CustomUserSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name']


class DoctorSimpleSerializer(serializers.ModelSerializer):
    user = CustomUserSimpleSerializer()

    class Meta:
        model = Doctor
        fields = ['user']


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['name']


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ['name', 'price']


#Записи на прием
class AppointmentAdminSerializer(serializers.ModelSerializer):
    date = serializers.DateField(format='%d-%m-%Y')
    time = serializers.TimeField(format='%H:%M')
    patient = PatientSimpleSerializer()
    doctor = DoctorSimpleSerializer()

    class Meta:
        model = Appointment
        fields = ['id', 'date', 'time', 'patient', 'doctor', 'payment']


#Добавление пациента
class PatientAdminCreateSerializer(serializers.ModelSerializer):
    date_birth = serializers.DateField(format='%d-%m_%Y')

    class Meta:
        model = Patient
        fields = ['id', 'first_name', 'last_name', 'date_birth', 'gender', 'phone_number']


class AppointmentPatientSerializer(serializers.ModelSerializer):
    patient = PatientAdminCreateSerializer()
    start_at = serializers.TimeField(format='%H:%M', input_formats=['%H:%M'])
    end_at = serializers.TimeField(format='%H:%M', input_formats=['%H:%M'])

    class Meta:
        model = Appointment
        fields = ['id', 'patient','doctor', 'registrar', 'department', 'service', 'status', 'start_at', 'end_at']


#ИНФО О ПАЦИЕНТЕ
class InfoAppointmentSerializer(serializers.ModelSerializer):
    registrar = CustomUserSimpleSerializer()
    doctor = DoctorSimpleSerializer()
    department =DepartmentSerializer()
    service = ServiceSerializer()

    class Meta:
        model = Appointment
        fields = ['registrar', 'doctor', 'start_at', 'end_at', 'status', 'department', 'service']


#История записей
class PatientAppointmentStatsSerializer(serializers.Serializer):
    total_appointments = serializers.SerializerMethodField()
    status_counts = serializers.SerializerMethodField()

    def get_total_appointments(self, obj):
        return Appointment.objects.filter(patient=obj).count()

    def get_status_counts(self, obj):
        patient = obj
        qs = Appointment.objects.filter(patient=patient)
        return qs.aggregate(
            waiting=Count('id', filter=Q(status='waiting')),
            reserved=Count('id', filter=Q(status='reserved')),
            cancelled=Count('id', filter=Q(status='cancelled')),
        )


class AppointmentHistorySerializer(serializers.ModelSerializer):
    registrar = CustomUserSimpleSerializer()
    date = serializers.DateField(format='%d-%m-%Y')
    time = serializers.TimeField(format='%H:%M')
    doctor = DoctorSimpleSerializer()
    department = DepartmentSerializer()
    service = ServiceSerializer()
    delete_url = serializers.SerializerMethodField()

    class Meta:
        model = Appointment
        fields = ['id', 'registrar', 'department', 'doctor', 'service', 'date', 'time', 'status', 'delete_url']

    def get_delete_url(self, obj):
        return f"/appointment/admin/{obj.id}/history/{obj.id}/delete/"


class PatientAppointmentsFullSerializer(serializers.Serializer):
    appointments = serializers.SerializerMethodField()
    summary = serializers.SerializerMethodField()

    def get_appointments(self, obj):
        appointments = Appointment.objects.filter(patient=obj)
        return AppointmentHistorySerializer(appointments, many=True).data

    def get_summary(self, obj):
        return PatientAppointmentStatsSerializer(obj).data


#История приемов
class AppointmentWaitingHistorySerializer(serializers.ModelSerializer):
    registrar = CustomUserSimpleSerializer()
    date = serializers.DateField(format='%d-%m-%Y')
    time = serializers.TimeField(format='%H:%M')
    doctor = DoctorSimpleSerializer()
    department = DepartmentSerializer()
    service = ServiceSerializer()

    class Meta:
        model = Appointment
        fields = ['id', 'registrar', 'department', 'doctor', 'service', 'date', 'time', 'status']


class PatientWaitingAppointmentsFullSerializer(serializers.Serializer):
    appointments = serializers.SerializerMethodField()
    summary = serializers.SerializerMethodField()

    def get_appointments(self, obj):
        waiting_appointments = obj.appointments.filter(status='waiting')
        return AppointmentWaitingHistorySerializer(waiting_appointments, many=True).data

    def get_summary(self, obj):
        return PatientAppointmentStatsSerializer(obj).data


#Оплата
class AppointmentSimpleSerializer(serializers.ModelSerializer):
    department = DepartmentSerializer()
    service = ServiceSerializer()

    class Meta:
        model = Appointment
        fields = ['department', 'doctor', 'service', 'date', 'time', 'payment', 'price']


class PatientPaymentReportSerializer(serializers.Serializer):
    appointments = serializers.SerializerMethodField()
    total_paid = serializers.SerializerMethodField()
    payment_method_sums = serializers.SerializerMethodField()

    def get_appointments(self, obj):
        qs = Appointment.objects.filter(patient=obj)
        return AppointmentSimpleSerializer(qs, many=True).data

    def get_total_paid(self, obj):
        return Appointment.objects.filter(patient=obj).aggregate(
            total=Sum('price')
        )['total'] or 0

    def get_payment_method_sums(self, obj):
        qs = Appointment.objects.filter(patient=obj)
        data = qs.values('payment').annotate(total=Sum('price'))
        return {item['payment']: item['total'] for item in data}


#Данные пациента
class InfoPatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = ['first_name' ,'last_name', 'phone_number', 'gender']


#Список врачей
class DoctorsSerializer(serializers.ModelSerializer):
    user = CustomUserSimpleSerializer()
    department = DepartmentSerializer()

    class Meta:
        model = Doctor
        fields = ['id', 'user', 'cabinet', 'department', 'phone_number']


#Добавление врача
class DoctorCreateSerializer(serializers.ModelSerializer):
    user = CustomUserSimpleSerializer()
    department = DepartmentSerializer()

    class Meta:
        model = Doctor
        fields = ['id', 'user', 'image', 'department', 'job_title', 'phone_number', 'email']


#Сохранение врача
class DoctorSaveSerializer(serializers.ModelSerializer):
    user = CustomUserSimpleSerializer()
    department = DepartmentSerializer()

    class Meta:
        model = Doctor
        fields = ['id', 'user', 'email', 'phone_number', 'department', 'job_title', 'bonus']


#Подробный отчет
class DoctorAppointmentSerializer(serializers.ModelSerializer):
    patient = PatientSimpleSerializer()
    service = ServiceSerializer()
    discount_price = serializers.SerializerMethodField()
    bonus = serializers.SerializerMethodField()

    class Meta:
        model = Appointment
        fields = ['id', 'date', 'patient', 'service', 'payment', 'price', 'discount_price', 'bonus']

    def get_discount_price(self, obj):
        price = obj.price or 0
        discount = obj.discount or 0
        return round(price - (price * discount / 100), 2)

    def get_bonus(self, obj):
        if obj.doctor and hasattr(obj.doctor, 'bonus'):
            return obj.doctor.bonus
        return 0


class DoctorSummarySerializer(serializers.Serializer):
    total_price = serializers.SerializerMethodField()
    total_discounted_price = serializers.SerializerMethodField()
    total_bonus = serializers.SerializerMethodField()
    total_appointments = serializers.SerializerMethodField()
    payment_method_sums = serializers.SerializerMethodField()

    def get_total_price(self, obj):
        result = obj.get_appointments().aggregate(total=Sum('price'))
        return result['total'] or 0

    def get_total_discounted_price(self, obj):
        discounted_sum = obj.get_appointments().aggregate(
            total=Sum(
                ExpressionWrapper(
                    F('price') - (F('price') * F('discount') / 100.0),
                    output_field=FloatField()
                )
            )
        )
        return discounted_sum['total'] or 0

    def get_total_bonus(self, obj):
        total_discounted = self.get_total_discounted_price(obj)
        doctor_bonus = obj.bonus or 0
        return round(total_discounted * (doctor_bonus / 100.0), 2)

    def get_total_appointments(self, obj):
        return obj.get_appointments().count()

    def get_payment_method_sums(self, obj):
        qs = obj.get_appointments()
        payments = qs.values('payment').annotate(total=Sum('price'))
        return {item['payment']: item['total'] for item in payments}


class DoctorAppointmentsFullSerializer(serializers.Serializer):
    appointments = serializers.SerializerMethodField()
    summary = serializers.SerializerMethodField()

    def get_appointments(self, obj):
        appointments = Appointment.objects.filter(doctor=obj)
        return DoctorAppointmentSerializer(appointments, many=True).data

    def get_summary(self, obj):
        return DoctorSummarySerializer(obj).data


#по врачам (процент врачам)
class DoctorDailyBonusSerializer(serializers.ModelSerializer):
    doctor_name = serializers.SerializerMethodField()
    cabinet = serializers.IntegerField(source='doctor.cabinet')
    bonus = serializers.SerializerMethodField()

    class Meta:
        model = Appointment
        fields = ['id', 'doctor_name', 'cabinet', 'date', 'bonus']

    def get_doctor_name(self, obj):
        return f"{obj.doctor.user.last_name} {obj.doctor.user.first_name}"

    def get_bonus(self, obj):
        bonus_percent = Decimal(getattr(obj.doctor, 'bonus', 0))
        price = Decimal(obj.price or 0)
        discount = Decimal(obj.discount or 0)
        discounted_price = price - (price * discount / Decimal(100))
        return round(discounted_price * bonus_percent / Decimal(100), 2)


#Сводный отчет
class ClinicSummaryReportSerializer(serializers.ModelSerializer):
    total_cash = serializers.SerializerMethodField()
    total_card = serializers.SerializerMethodField()
    doctor_cash_total = serializers.SerializerMethodField()
    doctor_card_total = serializers.SerializerMethodField()
    clinic_cash_total = serializers.SerializerMethodField()
    clinic_card_total = serializers.SerializerMethodField()

    class Meta:
        model = Appointment
        fields = [
            'total_cash', 'total_card',
            'doctor_cash_total', 'doctor_card_total',
            'clinic_cash_total', 'clinic_card_total',
        ]

    def get_total_cash(self, obj):
        return Appointment.total_sum_by_payment('наличные')

    def get_total_card(self, obj):
        return Appointment.total_sum_by_payment('безналичные(карта)')

    def get_doctor_cash_total(self, obj):
        return Appointment.doctor_sum_by_payment('наличные')

    def get_doctor_card_total(self, obj):
        return Appointment.doctor_sum_by_payment('безналичные(карта)')

    def get_clinic_cash_total(self, obj):
        return Appointment.clinic_sum_by_payment('наличные')

    def get_clinic_card_total(self, obj):
        return Appointment.clinic_sum_by_payment('безналичные(карта)')


# Управление календарем
class DoctorSimpleScheduleSerializer(serializers.ModelSerializer):
    user = CustomUserSimpleSerializer()
    department = DepartmentSerializer()

    class Meta:
        model = Doctor
        fields = ['user', 'image', 'speciality', 'department']


class AppointmentScheduleSerializer(serializers.ModelSerializer):
    start_at = serializers.TimeField(format='%H:%M')
    end_at = serializers.TimeField(format='%H:%M')

    class Meta:
        model = Appointment
        fields = ['start_at', 'end_at', 'status']


class DoctorScheduleSerializer(serializers.ModelSerializer):
    doctor = DoctorSimpleScheduleSerializer()
    appointment = AppointmentScheduleSerializer()

    class Meta:
        model = DoctorSchedule
        fields = ['id', 'doctor', 'appointment']


#Прайс лист
class ServiceSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ['name', 'price']


class PriceListSerializer(serializers.ModelSerializer):
    services = ServiceSimpleSerializer(read_only=True, many=True)

    class Meta:
        model = Department
        fields = ['id', 'name', 'services']