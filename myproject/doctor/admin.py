from django.contrib import admin
from .models import *

admin.site.register(Department)
admin.site.register(Patient)
admin.site.register(Doctor)
admin.site.register(DoctorSchedule)
admin.site.register(Appointment)
admin.site.register(Service)