# accounts/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import UserActivity

User = get_user_model()

@receiver(post_save, sender=User)
def create_user_activity(sender, instance, created, **kwargs):
    """Create user activity when user is created"""
    if created:
        UserActivity.objects.create(
            user=instance,
            action='ACCOUNT_CREATED',
            ip_address='N/A',
            user_agent='System'
        )
