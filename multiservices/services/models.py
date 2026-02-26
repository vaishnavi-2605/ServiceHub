from django.db import models
from django.conf import settings


# Create your models here.
class Service(models.Model):
    provider = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="services"
    )

    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    available_time = models.CharField(max_length=120, blank=True)
    available_days = models.CharField(max_length=64, blank=True)
    image = models.ImageField(upload_to='services/images/', blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.provider.username}"
