from django.db import models
from django.conf import settings


# Create your models here.
class Notification(models.Model):

    provider = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='provider_notifications',
        null=True,
        blank=True,
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='user_notifications',
        null=True,
        blank=True,
    )

    booking = models.ForeignKey(
        'booking.Booking',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    message = models.CharField(max_length=255)

    is_read = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.message
