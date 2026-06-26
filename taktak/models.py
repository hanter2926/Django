from django.db import models
from django.contrib.auth.models import User

class Announcement(models.Model):
    title = models.CharField(max_length=100)
    message = models.TextField()
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.title
        from django.db import models

class TeamMember(models.Model):
    employee_image=models.ImageField(upload_to='team/')
    employee_name=models.CharField(max_length=100)
    role=models.CharField(max_length=100)
    description=models.TextField()

    def __str__(self):
        return self.employee_name

class Gallery(models.Model):

    image=models.ImageField(upload_to='gallery/')
    title=models.CharField(max_length=100)

    def __str__(self):
        return self.title


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    mobile_number = models.CharField(max_length=15, unique=True)
    otp = models.CharField(max_length=6, blank=True, null=True) # OTP save karne ke liye

    def __str__(self):
        return self.user.username