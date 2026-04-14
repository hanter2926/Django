# Register your models here.

from django.contrib import admin
from .models import Category, Product # Dono models ko import karein
admin.site.register(Category)
admin.site.register(Product)



