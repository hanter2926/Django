from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Announcement,
    Category,
    ContactMessage,
    GalleryImage,
    Order,
    OrderItem,
    Product,
    StockHistoryLog,
    SystemLog,
    TeamMember,
    UserProfile,
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    list_display = ('name', 'slug')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    list_display = (
        'name',
        'sku_number',
        'category',
        'original_price',
        'price',
        'discount_percentage',
        'stock',
        'low_stock_threshold',
        'stock_status',
        'low_stock_alert',
    )
    list_filter = ('category', 'is_featured', 'is_out_of_stock')
    actions = ('bulk_restock_100',)

    def bulk_restock_100(self, request, queryset):
        updated = 0
        for product in queryset:
            original_stock = product.stock
            product.adjust_stock(100, user=request.user, note='Admin bulk restock +100')
            updated += 1
            SystemLog.objects.create(
                order=None,
                event_type='Bulk restock',
                details=f'Product {product.name} restocked from {original_stock} to {product.stock}.',
                created_by=request.user,
            )
        self.message_user(request, f'{updated} product(s) restocked by 100 units.')
    bulk_restock_100.short_description = 'Restock selected products with 100 units'

    def low_stock_alert(self, obj):
        if obj.stock <= obj.low_stock_threshold:
            return True
        return False
    low_stock_alert.boolean = True
    low_stock_alert.short_description = 'Low stock?'

    def stock_status(self, obj):
        if obj.is_out_of_stock:
            return format_html('<span style="color:#dc2626;font-weight:700;">Out of stock</span>')
        if obj.stock <= obj.low_stock_threshold:
            return format_html('<span style="color:#f59e0b;font-weight:700;">Low stock</span>')
        return format_html('<span style="color:#22c55e;font-weight:700;">In stock</span>')
    stock_status.short_description = 'Stock status'


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('message', 'is_active', 'created_at')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'phone')


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'created_at')


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ('employee_name', 'role')


@admin.register(GalleryImage)
class GalleryImageAdmin(admin.ModelAdmin):
    list_display = ('title', 'caption', 'created_at')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'customer_name',
        'email',
        'status',
        'payment_status',
        'delivery_date',
        'date_change_requested',
        'location_change_requested',
        'created_at',
    )
    list_filter = ('status', 'payment_status', 'date_change_requested', 'location_change_requested')
    actions = ('approve_date_change', 'approve_location_change', 'reject_date_change', 'reject_location_change')

    def approve_date_change(self, request, queryset):
        for order in queryset.filter(date_change_requested=True, requested_delivery_date__isnull=False):
            old_date = order.delivery_date
            order.delivery_date = order.requested_delivery_date
            order.date_change_requested = False
            order.requested_delivery_date = None
            order.save(update_fields=['delivery_date', 'date_change_requested', 'requested_delivery_date'])
            SystemLog.objects.create(
                order=order,
                event_type='Delivery date approved',
                details=f'Delivery date updated from {old_date} to {order.delivery_date}.',
                created_by=request.user,
            )
    approve_date_change.short_description = 'Approve selected delivery date change requests'

    def approve_location_change(self, request, queryset):
        for order in queryset.filter(location_change_requested=True).exclude(requested_delivery_location=''):
            old_location = order.delivery_location
            order.delivery_location = order.requested_delivery_location
            order.location_change_requested = False
            order.requested_delivery_location = ''
            order.save(update_fields=['delivery_location', 'location_change_requested', 'requested_delivery_location'])
            SystemLog.objects.create(
                order=order,
                event_type='Delivery location approved',
                details=f'Delivery location updated from "{old_location}" to "{order.delivery_location}".',
                created_by=request.user,
            )
    approve_location_change.short_description = 'Approve selected delivery location change requests'

    def reject_date_change(self, request, queryset):
        for order in queryset.filter(date_change_requested=True):
            order.date_change_requested = False
            order.requested_delivery_date = None
            order.save(update_fields=['date_change_requested', 'requested_delivery_date'])
            SystemLog.objects.create(
                order=order,
                event_type='Delivery date rejected',
                details='Requested delivery date change was rejected by the administrator.',
                created_by=request.user,
            )
    reject_date_change.short_description = 'Reject selected delivery date change requests'

    def reject_location_change(self, request, queryset):
        for order in queryset.filter(location_change_requested=True):
            order.location_change_requested = False
            order.requested_delivery_location = ''
            order.save(update_fields=['location_change_requested', 'requested_delivery_location'])
            SystemLog.objects.create(
                order=order,
                event_type='Delivery location rejected',
                details='Requested delivery location change was rejected by the administrator.',
                created_by=request.user,
            )
    reject_location_change.short_description = 'Reject selected delivery location change requests'


@admin.register(StockHistoryLog)
class StockHistoryLogAdmin(admin.ModelAdmin):
    list_display = ('product', 'quantity_change', 'resulting_stock', 'changed_by', 'timestamp')
    list_filter = ('changed_by',)
    search_fields = ('product__name', 'note')


@admin.register(SystemLog)
class SystemLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'order', 'event_type', 'created_by')
    list_filter = ('event_type', 'created_by')
    search_fields = ('details', 'order__customer_name', 'order__id')
