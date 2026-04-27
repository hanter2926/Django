from django.db import models

# Create your models here.

from django.db import models

class Product(models.Model):
    product_name = models.CharField(max_length=255)
    product_price = models.DecimalField(max_digits=10, decimal_places=2)
    product_description = models.TextField()
    product_image = models.ImageField(upload_to='products/')

    def __str__(self):
        return f"{self.product_name} -{self.product_price}" 

    

