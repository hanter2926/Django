from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager

# --- 1. CUSTOM USER MANAGER (Yeh superuser error ko theek karega) ---
class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not False:
            pass
        if extra_fields.get('is_superuser') is not False:
            pass

        return self.create_user(email, password, **extra_fields)


# --- 2. CUSTOM USER MODEL ---
class CustomUser(AbstractUser):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    
    username = None # Username hata diya
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255)
    mobile_no = models.CharField(max_length=15)
    alternate_mobile_no = models.CharField(max_length=15, blank=True, null=True)
    dob = models.DateField(verbose_name="Date of Birth", blank=True, null=True)
    address = models.TextField()
    profile_image = models.ImageField(upload_to="profile_pics/", blank=True, null=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)

    # Django ko batana ki custom manager use karein
    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name', 'mobile_no'] # Isme username nahi hona chahiye

    def __str__(self):
        return self.email


# --- 3. CATEGORY MODEL ---
class Category(models.Model):
    category_name = models.CharField(max_length=100)
    category_image = models.ImageField(upload_to="category_pics/")
    category_product_stock = models.PositiveIntegerField(default=0, verbose_name="Quantity")

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.category_name


# --- 4. PRODUCT MODEL ---
class Product(models.Model):
    product_name = models.CharField(max_length=255)
    product_image = models.ImageField(upload_to="product_pics/")
    product_description = models.TextField()
    product_category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="products")
    
    product_original_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Original Price (CP)")
    product_sale_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Sale Price (SP)")
    
    top_product = models.BooleanField(default=False, verbose_name="Top Product")
    best_seller = models.BooleanField(default=False, verbose_name="Best Seller")
    limited_offer = models.BooleanField(default=False, verbose_name="Limited Offer/Deal")

    def __str__(self):
        return self.product_name

    @property
    def discount_percentage(self):
        if self.product_original_price > 0 and self.product_sale_price < self.product_original_price:
            cp = float(self.product_original_price)
            sp = float(self.product_sale_price)
            discount = ((cp - sp) / cp) * 100
            return round(discount)
        return 0