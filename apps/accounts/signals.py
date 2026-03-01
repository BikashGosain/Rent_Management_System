from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User


@receiver(post_save, sender=User)
def set_superuser_role(sender, instance, created, **kwargs):
    """Automatically set role=admin for superusers."""
    if instance.is_superuser and instance.role != 'admin':
        User.objects.filter(pk=instance.pk).update(role='admin')