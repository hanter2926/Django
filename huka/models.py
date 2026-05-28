from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

# 1. USER PROFILE MODEL (Coins aur Level 100 System ke liye)
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    # Level 1 se 100 tak hi ho sakega
    current_level = models.IntegerField(
        default=1, 
        validators=[MinValueValidator(1), MaxValueValidator(100)]
    )
    total_coins = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    avatar_url = models.URLField(blank=True, null=True) # Google/FB profile pic ke liye

    def __str__(self):
        return f"{self.user.username} - Level: {self.current_level} - Coins: {self.total_coins}"

    # Level complete hone par Django backend se coins badhane ka method
    def complete_level(self):
        if self.current_level < 100:
            self.current_level += 1
            self.total_coins += 15  # Har level clear hone par 15 coins reward
            self.save()
            return True
        return False


# 2. FRIEND SYSTEM MODEL (Send/Accept Request ke liye)
class Friendship(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]

    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_requests")
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name="received_requests")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Ek user dusre ko ek hi baar request bhej sake, duplicate na ho
        unique_together = ('sender', 'receiver')

    def __str__(self):
        return f"{self.sender.username} -> {self.receiver.username} ({self.status})"


# 3. CHAT SYSTEM MODEL (Friends Chat ke liye)
class ChatMessage(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sender_messages")
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name="receiver_messages")
    message_text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['timestamp'] # Messages hamesha time ke hisab se order honge

    def __str__(self):
        return f"From {self.sender.username} to {self.receiver.username} at {self.timestamp}"



