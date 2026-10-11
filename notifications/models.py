from django.db import models
from django.conf import settings
from bookings.models import Booking

class Notification(models.Model):
    class NotificationType(models.TextChoices):
        BOOKING_REQUEST = 'REQUEST', 'New Consultation Request'
        BOOKING_CONFIRMED = 'CONFIRMED', 'Booking Confirmed'
        BOOKING_DECLINED = 'DECLINED', 'Booking Declined'
        BOOKING_CANCELLED = 'CANCELLED', 'Booking Cancelled'
        SESSION_REMINDER = 'REMINDER', 'Upcoming Consultation Reminder'
        RECORD_ADDED = 'RECORD', 'Session Advice Published'

    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NotificationType.choices)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"To {self.recipient.username}: {self.title}"
