import random
import string
from datetime import timedelta
from decimal import Decimal
from urllib.parse import quote_plus

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone


def default_delivery_date():
    return timezone.now().date() + timedelta(days=5)


def generate_sku_number():
    prefix = 'TAKTK'
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    return f'{prefix}-{code}'


class Review(models.Model):
    product = models.ForeignKey('Product', related_name='reviews', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(default=5)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('product', 'user')

    def __str__(self):
        return f'{self.user.username} - {self.product.name}'


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    sku_number = models.CharField(max_length=20, unique=True, blank=True)
    description = models.TextField(blank=True)
    original_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_percentage = models.PositiveSmallIntegerField(
        default=10,
        validators=[MinValueValidator(10), MaxValueValidator(30)],
        help_text='Discount percentage between 10 and 30.',
    )
    stock = models.PositiveIntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(default=5)
    is_out_of_stock = models.BooleanField(default=False)
    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.sku_number:
            self.sku_number = generate_sku_number()
        if self.original_price == Decimal('0.00'):
            self.original_price = self.price
        self.price = self.discounted_price
        self.is_out_of_stock = self.stock == 0
        super().save(*args, **kwargs)

    @property
    def discounted_price(self):
        return (self.original_price * (Decimal('100') - Decimal(self.discount_percentage)) / Decimal('100')).quantize(Decimal('0.01'))

    @property
    def savings_amount(self):
        return (self.original_price - self.discounted_price).quantize(Decimal('0.01'))

    @property
    def discount_badge(self):
        return f'Save {self.discount_percentage}% Today!'

    @property
    def display_image_url(self):
        if self.image and hasattr(self.image, 'url'):
            return self.image.url
        query = quote_plus('+'.join(self.name.split()))
        return f'https://source.unsplash.com/900x900/?{query},premium,retail,product'

    def adjust_stock(self, quantity_change, user=None, note=''):
        original_stock = self.stock
        self.stock = max(0, self.stock + quantity_change)
        self.is_out_of_stock = self.stock == 0
        self.save(update_fields=['stock', 'is_out_of_stock'])
        StockHistoryLog.objects.create(
            product=self,
            changed_by=user,
            quantity_change=quantity_change,
            resulting_stock=self.stock,
            note=note or f'Stock changed by {quantity_change}.',
        )
        return original_stock, self.stock

    def get_absolute_url(self):
        return reverse('product_detail', args=[self.slug])


class Announcement(models.Model):
    message = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.message


class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    full_name = models.CharField(max_length=150, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    pincode = models.CharField(max_length=20, blank=True)
    avatar_image = models.URLField(blank=True, help_text='Optional URL for user profile thumbnail')
    bio = models.TextField(blank=True)

    @property
    def profile_picture_url(self):
        if self.avatar_image:
            return self.avatar_image
        query = quote_plus('+'.join((self.full_name or self.user.username).split()))
        return f'https://images.unsplash.com/photo-1552058544-f2b08422138a?auto=format&fit=crop&w=120&q=80'

    def __str__(self):
        return self.full_name or self.user.username


class ContactMessage(models.Model):
    name = models.CharField(max_length=150)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.name} - {self.subject}'


class TeamMember(models.Model):
    employee_image = models.ImageField(upload_to='team/', blank=True, null=True)
    employee_name = models.CharField(max_length=150)
    role = models.CharField(max_length=150)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.employee_name


class GalleryImage(models.Model):
    image = models.ImageField(upload_to='gallery/')
    title = models.CharField(max_length=150, blank=True)
    caption = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title or 'Gallery image'


class Order(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Shipped', 'Shipped'),
        ('Delivered', 'Delivered'),
    ]
    PAYMENT_STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Paid', 'Paid'),
        ('Failed', 'Failed'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    customer_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField()
    city = models.CharField(max_length=100)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    items = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    payment_method = models.CharField(max_length=20, default='card')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='Pending')
    razorpay_order_id = models.CharField(max_length=255, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=255, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=255, blank=True, null=True)
    delivery_date = models.DateField(default=default_delivery_date)
    delivery_location = models.CharField(max_length=255, blank=True)
    date_change_requested = models.BooleanField(default=False)
    requested_delivery_date = models.DateField(null=True, blank=True)
    location_change_requested = models.BooleanField(default=False)
    requested_delivery_location = models.CharField(max_length=255, blank=True)
    tracking_state = models.CharField(
        max_length=20,
        choices=[
            ('Processed', 'Processed'),
            ('Transit', 'Transit'),
            ('Delivered', 'Delivered'),
        ],
        default='Processed'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Order #{self.id} - {self.customer_name}'


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items_set', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    product_name = models.CharField(max_length=200)
    product_slug = models.SlugField(blank=True)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.product_name


class StockHistoryLog(models.Model):
    product = models.ForeignKey(Product, related_name='stock_history', on_delete=models.CASCADE)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    quantity_change = models.IntegerField()
    resulting_stock = models.PositiveIntegerField()
    note = models.CharField(max_length=255, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f'{self.product.name} change {self.quantity_change} at {self.timestamp:%Y-%m-%d %H:%M}'


class SystemLog(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    order = models.ForeignKey(Order, related_name='system_logs', null=True, blank=True, on_delete=models.SET_NULL)
    event_type = models.CharField(max_length=100)
    details = models.TextField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f'{self.timestamp:%Y-%m-%d %H:%M} | {self.event_type}'
