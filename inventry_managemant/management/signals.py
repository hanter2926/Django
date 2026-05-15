from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import Profile

# Jab naya User banega, ye automatically Profile bana dega
@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

# Jab User save hoga, Profile bhi save ho jayegi
@receiver(post_save, sender=User)
def save_profile(sender, instance, **kwargs):
    instance.profile.save()