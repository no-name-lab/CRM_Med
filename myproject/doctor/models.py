from django.db import models
from reception.models import UserProfile, Department, Patient, Doctor, Service



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
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='department')
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='service')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='waiting')
    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.patient} → {self.doctor} on {self.date} at {self.start_time}-{self.end_time}"
