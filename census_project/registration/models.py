from django.db import models

class Citizen(models.Model):
    GENDER_CHOICES = [('M', 'Male'), ('F', 'Female'), ('O', 'Other')]
    
    name = models.CharField(max_length=100)
    aadhar_number = models.CharField(max_length=12, unique=True)
    pincode = models.CharField(max_length=6)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    state = models.CharField(max_length=50)
    district = models.CharField(max_length=50)
    address = models.TextField()
    phone_number = models.CharField(max_length=15)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return self.name