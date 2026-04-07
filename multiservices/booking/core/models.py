from django.db import models


class ContactMessage(models.Model):
    SUBJECT_CHOICES = [
        ('booking-support', 'Booking Support'),
        ('provider-information', 'Provider Information'),
        ('technical-issue', 'Technical Issue'),
        ('general-inquiry', 'General Inquiry'),
    ]

    name = models.CharField(max_length=120)
    email = models.EmailField()
    subject = models.CharField(max_length=40, choices=SUBJECT_CHOICES)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.get_subject_display()}"
