from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('user', 'User'),
        ('provider', 'Provider'),
    )
    PROVIDER_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    provider_status = models.CharField(max_length=20, choices=PROVIDER_STATUS_CHOICES, default='approved')
    mobile_no = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)

    def is_provider(self):
        return self.role == 'provider'

    def is_user(self):
        return self.role == 'user'


class ProviderProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    phone = models.CharField(max_length=15)
    address = models.TextField(blank=True)
    experience = models.IntegerField(default=0)
    bio = models.TextField(blank=True)
    profile_image = models.ImageField(upload_to='providers/images/', blank=True)
    certificate = models.FileField(upload_to='providers/certificates/', blank=True, null=True)
    aadhaar_card = models.FileField(upload_to='providers/aadhaar/', blank=True, null=True)

    def __str__(self):
        return self.user.first_name or self.user.username
