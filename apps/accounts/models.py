from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.
 
class User(AbstractUser):
    ROLES = [
        ('admin',  'Admin'),
        ('owner',  'House Owner'),
        ('tenant', 'Tenant'),
    ]
    role  = models.CharField(choices=ROLES, max_length=20, default='tenant')
    phone = models.CharField(max_length=15, blank=True)
    photo = models.ImageField(upload_to='users/', blank=True, null=True)
 
    def is_admin(self):  return self.role == 'admin'  or self.is_superuser
    def is_owner(self):  return self.role == 'owner'
    def is_tenant(self): return self.role == 'tenant'
 
    def __str__(self): return f'{self.username} ({self.role})'
