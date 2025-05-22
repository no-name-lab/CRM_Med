from django.contrib import admin
from .models import *

admin.site.register(CustomerRecord)
admin.site.register(Patient)
admin.site.register(Doctor)
admin.site.register(Department)
admin.site.register(Reception)
admin.site.register(Service)
admin.site.register(HistoryRecord)
admin.site.register(PriceList)
