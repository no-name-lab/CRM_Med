from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.validators import MinValueValidator, MaxValueValidator
from phonenumber_field.modelfields import PhoneNumberField
from django.db import models
from django.contrib.auth.base_user import BaseUserManager
from django.utils import timezone
from datetime import timedelta


ROLE_CHOICES = (
    ('Admin', 'admin'),
    ('Reception', 'reception'),
    ('Doctor', 'doctor')
)
GENDER_CHOICES = (
    ('Male', 'male'),
    ('Female', 'female')
)


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email обязателен")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("У суперпользователя должен быть is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("У суперпользователя должен быть is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class EmailLoginCode(models.Model):
    email = models.EmailField()
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_valid(self):
        return timezone.now() < self.created_at + timedelta(minutes=5)  # 5 минут срок


class UserProfile(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    phone_number = PhoneNumberField(region='KG', null=True, blank=True)
    first_name = models.CharField(max_length=60, blank=True)
    last_name = models.CharField(max_length=60, blank=True)
    age = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(140)],
                                           null=True, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    gender = models.CharField(max_length=32, choices=GENDER_CHOICES)
    role = models.CharField(max_length=32, choices=ROLE_CHOICES)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def __str__(self):
        return f"{self.email} ({self.role})"


class Department(models.Model):
    name = models.CharField(max_length=64)

    def __str__(self):
        return self.name


class Doctor(UserProfile):
    speciality = models.CharField(max_length=256)
    medical_license = models.CharField(max_length=256, null=True, blank=True )
    bonus = models.PositiveIntegerField(default=0, null=True, blank=True)
    image = models.ImageField(upload_to='doctor_img/', null=True, blank=True)
    departament = models.ForeignKey(Department, related_name='departament_doctor', on_delete=models.CASCADE, null=True,
                                    blank=True)
    cabinet = models.SmallIntegerField()

    class Meta:
         verbose_name = "Doctor"

    def __str__(self):
        return f"Dr. {self.first_name} {self.last_name} {self.cabinet} {self.speciality}"


class Reception(UserProfile):
    desk_name = models.CharField(max_length=50)

    class Meta:
         verbose_name = "Reception"

    def __str__(self):
        return f"Reception - {self.email}"


class Service(models.Model):
    name = models.CharField(max_length=64)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="services")
    price = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.name


class Patient(models.Model):
    GENDER_CHOICES = (
        ('male', 'Мужской'),
        ('female', 'Женский'),
    )
    full_name = models.CharField(max_length=64)
    date_birth = models.DateField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='patient_depart', null=True, blank=True)
    service = models.ForeignKey(Service, on_delete=models.CASCADE, null=True, blank=True)
    doctor = models.ForeignKey(Doctor, related_name='doctor_for_patientcreate', on_delete=models.CASCADE,
                               null=True, blank=True)
    phone_number = PhoneNumberField(region='KG')
    reception = models.ForeignKey(Reception, related_name='reception_patient', on_delete=models.CASCADE, null=True,  blank=True)
    STATUS_CHOICES = (
        ('Живая очередь', 'Живая очередь'),
        ('Предзапись', 'Предзапись'),
        ('Отменено', 'Отменено'),
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Предзапись')
    user = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name="patient_profile", null=True, blank=True)

    def __str__(self):
        return f"{self.full_name}"


class CustomerRecord(models.Model):
    reception = models.ForeignKey(Reception, related_name='reception_customer', on_delete=models.CASCADE,
                                  null=True, blank=True)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='customer_record', null=True, blank=True)
    doctor = models.ForeignKey(Doctor, related_name='doctor_customer', on_delete=models.CASCADE, null=True, blank=True)
    service = models.ForeignKey(Service, on_delete=models.CASCADE, null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, null=True, blank=True, related_name='cust_dep')
    price = models.PositiveIntegerField(default=0, null=True, blank=True)
    change = models.PositiveIntegerField(null=True, blank=True)
    PAYMENT_CHOICES = (
        ('cash', 'Наличные'),
        ('card', 'Карта'),
    )
    payment_type = models.CharField(max_length=10, choices=PAYMENT_CHOICES, default='cash', null=True, blank=True)
    created_date = models.DateTimeField(auto_now_add=True)
    STATUS_CHOICES = (
        ('Живая очередь', 'Живая очередь'),
        ('Предзапись', 'Предзапись'),
        ('Отменено', 'Отменено'),
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Живая очередь')
    CHOICES_RECORD = (
        ('был в приеме', 'был в приеме'),
        ('в ожидании', 'в ожидании'),
        ('отменен', 'отменен'),
    )
    records = models.CharField(max_length=16, choices=CHOICES_RECORD, default='был в приеме')
    phone_number = PhoneNumberField(region='KG', null=True, blank=True)
    time = models.TimeField(null=True, blank=True)  # расширение времени
    discount = models.PositiveIntegerField(default=0)

    def get_total_records(self):
        from .models import HistoryRecord
        return HistoryRecord.objects.filter(patient=self.patient).count()

    def get_was_on_reception(self):
        from .models import HistoryRecord
        return HistoryRecord.objects.filter(patient=self.patient, record='был в приеме').count()

    def __str__(self):
            return f"Invoice for {self.patient}"


class HistoryRecord(models.Model):
    patient = models.ForeignKey(Patient, related_name='patient_history', on_delete=models.CASCADE)
    reception = models.ForeignKey(Reception, related_name='reception_history', on_delete=models.CASCADE)
    departament = models.ForeignKey(Department, related_name='departament_history', on_delete=models.CASCADE)
    doctor = models.ForeignKey(Doctor, related_name='doctor_history', on_delete=models.CASCADE)
    service = models.ForeignKey(Service, related_name='service_history', on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    CHOICES_RECORD = (
        ('был в приеме', 'был в приеме'),  #был в приеме фильтрация
        ('в ожидании', 'в ожидании'),
        ('отменен', 'отменен'),
    )
    record = models.CharField(max_length=16, choices=CHOICES_RECORD, default='в ожидании')
    payment = models.ForeignKey(CustomerRecord, related_name='payment_history', on_delete=models.CASCADE)
    description = models.TextField()

    def __str__(self):
        return f'{self.patient}'


class PriceList(models.Model):
    department = models.ForeignKey(Department, related_name='departament_price_list', on_delete=models.CASCADE)
    service = models.ForeignKey(Service, related_name='price_service', on_delete=models.CASCADE)
    price = models.PositiveIntegerField()

    def __str__(self):
        return f'{self.department}'

