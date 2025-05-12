from django.contrib.auth.models import AbstractUser
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField
from django.core.validators import MaxValueValidator, MinValueValidator

ROLES = (
    ('admin', 'admin'),
    ('doctor', 'doctor'),
    ('reception', 'reception'),
)

class UserProfile(AbstractUser):
    email = models.EmailField(unique=True)
    phone_number = PhoneNumberField(region='KG')
    age = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(18), MaxValueValidator(99)],
        null=True, blank=True
    )
    profile_image = models.ImageField(upload_to='profiles/', null=True, blank=True)
    role = models.CharField(max_length=32, choices=ROLES, default='doctor')

    REQUIRED_FIELDS = ['email', 'phone_number']

    def __str__(self):
        return f"{self.email} ({self.role})"


class Department(models.Model):
    name = models.CharField(max_length=64)

    def __str__(self):
        return self.name


class Doctor(UserProfile):
    speciality = models.CharField(max_length=256)
    medical_license = models.CharField(max_length=256)
    bonus = models.PositiveIntegerField(default=0)
    # бонусту общий суммадан кемитуу % менен
    image = models.ImageField(upload_to='doctor_img/', null=True, blank=True)
    departament = models.ForeignKey(Department, related_name='departament_doctor', on_delete=models.CASCADE)
    cabinet = models.SmallIntegerField()


    def __str__(self):
        return f"Dr. {self.first_name} {self.last_name}"


class Reception(UserProfile):
    desk_name = models.CharField(max_length=50)

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
    first_name = models.CharField(max_length=64)
    last_name = models.CharField(max_length=64)
    date_birth = models.DateField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class CustomerRecord(models.Model):
    reception = models.ForeignKey(Reception, related_name='reception_customer', on_delete=models.CASCADE)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    doctor = models.ForeignKey(Doctor, related_name='doctor_customer', on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True)
    price = models.PositiveIntegerField(default=0)
    change = models.PositiveIntegerField()
    PAYMENT_CHOICES = (
        ('cash', 'Наличные'),
        ('card', 'Карта'),
    )
    payment_type = models.CharField(max_length=10, choices=PAYMENT_CHOICES, default='cash')
    date = models.DateTimeField(auto_now_add=True)
    STATUS_CHOICES = (
        ('waiting', 'Живая очередь'),
        ('reserved', 'Предзапись'),
        ('cancelled', 'Отменено'),
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='waiting')
    phone_number = PhoneNumberField(region='KG', null=True, blank=True)
    time = models.TimeField()  # расширение времени
    #  инфо о пациенте ушул класс мн берилет
    # сериалайзерге релитетнейм  мн доктордын ичинен запистерди фильтр кылуу


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
    record = models.CharField(max_length=10, choices=CHOICES_RECORD, default='в ожидании')
    payment = models.ForeignKey(CustomerRecord, related_name='payment_history', on_delete=models.CASCADE)
    description = models.TextField()

#     инфо о пациенте - оплата , тип и сумманы чыгарабыз


class PriceList(models.Model):
    department = models.ForeignKey(Department, related_name='departament_price_list', on_delete=models.CASCADE)
    service = models.ForeignKey(Service, related_name='price_service', on_delete=models.CASCADE)

