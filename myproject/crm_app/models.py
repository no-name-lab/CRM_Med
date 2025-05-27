from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Sum, ExpressionWrapper, F, FloatField
from phonenumber_field.modelfields import PhoneNumberField
from django.db import models
from reception.models import CustomerRecord, UserProfile


class DoctorAdmin(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='doctor_profile')
    phone_number = PhoneNumberField(region='KG', null=True, blank=True)
    job_title = models.CharField(max_length=34, null=True, blank=True)
    email = models.EmailField(unique=True, null=True, blank=True)

    # Подробный отчет
    def get_appointments(self):
        return CustomerRecord.objects.filter(doctor=self)

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
