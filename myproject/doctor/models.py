from django.db import models
from phonenumber_field.modelfields import PhoneNumberField
from django.core.validators import MaxValueValidator, MinValueValidator
from django.contrib.auth.models import AbstractUser

# Общие
class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('doctor', 'Doctor'),
        ('reception', 'Reception'),
    )
    email = models.EmailField(unique=True)
    phone_number = PhoneNumberField(region='KG')
    age = models.PositiveSmallIntegerField(validators=[MinValueValidator(18), MaxValueValidator(99)], null=True, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='doctor')
    profile_image = models.ImageField(upload_to='profiles/', null=True, blank=True)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'phone_number']

    def __str__(self):
        return f"{self.email} ({self.role})"


class Department(models.Model):
    name = models.CharField(max_length=64)

    def __str__(self):
        return self.name


class Service(models.Model):
    name = models.CharField(max_length=64)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="services")
    price = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.name


# Пациенты
class Patient(models.Model):
    GENDER_CHOICES = (
        ('male', 'Мужской'),
        ('female', 'Женский'),
    )
    first_name = models.CharField(max_length=64)
    last_name = models.CharField(max_length=64)
    date_birth = models.DateField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    phone_number = PhoneNumberField(region='KG', null=True, blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


# Доктор
class Doctor(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='doctor_profile')
    speciality = models.CharField(max_length=256)
    medical_license = models.CharField(max_length=256)
    bonus = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to='doctor_img/', null=True, blank=True)
    department = models.ForeignKey(Department, related_name='department_doctors', on_delete=models.CASCADE)
    cabinet = models.SmallIntegerField()

    def __str__(self):
        return f"Dr. {self.user.first_name} {self.user.last_name}"

    def get_schedule_for_day(self, date):
        return self.schedules.filter(date=date)


# Расписание доктора
class DoctorSchedule(models.Model):
    doctor = models.ForeignKey(Doctor, related_name='schedules', on_delete=models.CASCADE)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_available = models.BooleanField(default=True)

    class Meta:
        unique_together = ('doctor', 'date', 'start_time')

    def __str__(self):
        return f"{self.doctor} - {self.date} ({self.start_time}-{self.end_time})"


# --- Запись на прием ---
class Appointment(models.Model):
    STATUS_CHOICES = (
        ('waiting', 'Живая очередь'),
        ('reserved', 'Предзапись'),
        ('cancelled', 'Отменено'),
    )

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='appointments')
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    date = models.DateField()
    time = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='waiting')
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.patient} → {self.doctor} on {self.date} at {self.time}"
