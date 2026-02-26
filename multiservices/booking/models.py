from django.db import models
from django.conf import settings


# Create your models here.
class Booking(models.Model):

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
    )

    PAYMENT_MODE_CHOICES = (
        ('cash', 'Cash'),
        ('online', 'Online'),
    )

    PAYMENT_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('paid', 'Paid'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='user_bookings',
        on_delete=models.CASCADE
    )

    service = models.ForeignKey(
        'services.Service',
        on_delete=models.CASCADE,
        related_name='bookings',
    )

    provider = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='provider_bookings',
        on_delete=models.CASCADE
    )

    service_name = models.CharField(max_length=200)
    date = models.DateTimeField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    service_address = models.CharField(max_length=255, blank=True)
    use_live_location = models.BooleanField(default=False)
    latitude = models.DecimalField(max_digits=10, decimal_places=7, blank=True, null=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, blank=True, null=True)

    provider_latitude = models.DecimalField(max_digits=10, decimal_places=7, blank=True, null=True)
    provider_longitude = models.DecimalField(max_digits=10, decimal_places=7, blank=True, null=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    otp = models.CharField(
        max_length=4,
        blank=True,
        null=True
    )

    provider_marked_done = models.BooleanField(default=False)
    payment_mode = models.CharField(max_length=20, choices=PAYMENT_MODE_CHOICES, blank=True, null=True)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')

    feedback_rating = models.PositiveSmallIntegerField(blank=True, null=True)
    feedback_text = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.service_name} - {self.status}"


class BookingReport(models.Model):
    booking = models.ForeignKey('booking.Booking', on_delete=models.CASCADE, related_name='reports')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='submitted_booking_reports',
    )
    provider = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='provider_booking_reports',
    )
    reason = models.CharField(max_length=120)
    details = models.TextField(blank=True)
    is_reviewed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['booking', 'user'], name='unique_report_per_booking_user'),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"Report #{self.id} for booking #{self.booking_id}"
