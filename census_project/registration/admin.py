from django.contrib import admin
from .models import Citizen

@admin.register(Citizen)
class CitizenAdmin(admin.ModelAdmin):
    list_display = ('name', 'aadhar_number', 'phone_number', 'is_verified')
    list_filter = ('state', 'district')