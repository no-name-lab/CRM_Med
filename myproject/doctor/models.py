from django.db import models
from phonenumber_field.modelfields import PhoneNumberField
from django.core.validators import MaxValueValidator, MinValueValidator
from django.contrib.auth.models import AbstractUser, PermissionsMixin
from django.db.models import Sum, F, ExpressionWrapper, FloatField


# Общие
class CustomUser(AbstractUser, PermissionsMixin):
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

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

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
#admin models
    phone_number = PhoneNumberField(region='KG', null=True, blank=True)
    job_title = models.CharField(max_length=34, null=True, blank=True)
    email = models.EmailField(unique=True, null=True, blank=True)

    def __str__(self):
        return f"Dr. {self.user.first_name} {self.user.last_name}"

    def get_schedule_for_day(self, date):
        return self.schedules.filter(date=date)

    # Подробный отчет
    def get_appointments(self):
        return Appointment.objects.filter(doctor=self)

    def get_total_appointments(self):
        return self.get_appointments().count()

    def get_total_price(self):
        result = self.get_appointments().aggregate(total=Sum('price'))
        return result['total'] or 0

    def get_total_discounted_price(self):
        discounted_sum = self.get_appointments().aggregate(
            total=Sum(
                ExpressionWrapper(
                    F('price') - (F('price') * F('discount') / 100.0),
                    output_field=FloatField()
                )
            )
        )
        return discounted_sum['total'] or 0

    def get_total_bonus(self):
        # бонус считается от суммы со скидкой
        total_discounted = self.get_total_discounted_price()
        return round(total_discounted * (self.bonus / 100.0), 2)


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
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='services')
    date = models.DateField()
    time = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='waiting')
    notes = models.TextField(blank=True, null=True)
#admin models
    PAYMENT_CHOICES = (
        ('наличные', 'Наличные'),
        ('безналичные(карта)', 'Безналичные(карта)')
    )
    payment = models.CharField(choices=PAYMENT_CHOICES, max_length=33, default='наличные', null=True, blank=True)
    discount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    start_at = models.TimeField(default="10:00", null=True, blank=True)
    end_at = models.TimeField(default="10:00", null=True, blank=True)
    registrar = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='registrar_admin', null=True,
                                  blank=True)
    price = models.PositiveSmallIntegerField(default=0, null=True, blank=True)

    def __str__(self):
        return f"{self.patient} → {self.doctor} on {self.date} at {self.time}"

    # Оплата
    def get_payment_method_sums(patient, target_date):
        from .models import Appointment

        qs = Appointment.objects.filter(patient=patient, date=target_date)

        sums = (
            qs.values('payment')
            .annotate(total=Sum('price'))
        )

        return {entry['payment']: entry['total'] for entry in sums}

        payment_methods = {item['payment']: item['total'] for item in payment_breakdown}

        return {
            'total_price': total_price,
            'payment_methods': payment_methods
        }

    # Сводный отчет
    @classmethod
    def total_sum_by_payment(cls, method):
        return cls.objects.filter(payment=method).aggregate(total=Sum('price'))['total'] or 0

    @classmethod
    def doctor_sum_by_payment(cls, method, percent=0.9):
        return cls.objects.filter(payment=method).aggregate(
            total=Sum(F('price') * percent))['total'] or 0

    @classmethod
    def clinic_sum_by_payment(cls, method, percent=0.1):
        return cls.objects.filter(payment=method).aggregate(
            total=Sum(F('price') * percent))['total'] or 0


# Расписание доктора
class DoctorSchedule(models.Model):
    doctor = models.ForeignKey(Doctor, related_name='schedules', on_delete=models.CASCADE)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_available = models.BooleanField(default=True)
#admin models
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='appointments', null=True)

    class Meta:
        unique_together = ('doctor', 'date', 'start_time')

    def __str__(self):
        return f"{self.doctor} - {self.date} ({self.start_time}-{self.end_time})"