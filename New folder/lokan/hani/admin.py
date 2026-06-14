from django.contrib import admin
from .models import CustomUser, Category, Product

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ['email', 'full_name', 'mobile_no', 'gender']

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['category_name', 'category_product_stock']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['product_name', 'product_category', 'product_original_price', 'product_sale_price', 'top_product', 'best_seller', 'limited_offer']
    list_filter = ['top_product', 'best_seller', 'limited_offer', 'product_category']
    search_fields = ['product_name', 'product_description']
    
    # Groups the checkboxes together in the Admin panel Form
    fieldsets = [
        ('Product Details', {
            'fields': ['product_name', 'product_category', 'product_image', 'product_description']
        }),
        ('Pricing', {
            'fields': ['product_original_price', 'product_sale_price']
        }),
        ('Promotions & Sections (Checkboxes)', {
            'fields': ['top_product', 'best_seller', 'limited_offer']
        }),
    ]
