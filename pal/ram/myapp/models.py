from django.db import models

# 1. Category Model
class Category(models.Model):
    category_name = models.CharField(max_length=255)
    category_image = models.ImageField(upload_to='categories/', null=True, blank=True)

    def __str__(self):
        return self.category_name

# 2. Product Model
class Product(models.Model):
    # Category add karne ke liye ye ForeignKey sahi hai
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    product_name = models.CharField(max_length=255)
    product_price = models.DecimalField(max_digits=10, decimal_places=2)
    product_description = models.TextField()
    product_image = models.ImageField(upload_to='products/')

    def __str__(self):
        # Yahan self.ram ki jagah self.product_name likhein
        return self.product_name
