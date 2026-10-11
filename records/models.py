from django.db import models
from bookings.models import Booking

class SessionRecord(models.Model):
    class Attendance(models.TextChoices):
        ATTENDED = 'ATTENDED', 'Attended'
        NO_SHOW = 'NO_SHOW', 'No-Show'

    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='session_record')
    attendance = models.CharField(max_length=20, choices=Attendance.choices, default=Attendance.ATTENDED)
    
    advice_given = models.TextField(blank=True, help_text="Recommendations and guidance visible to the student")
    private_notes = models.TextField(blank=True, help_text="Confidential notes for faculty and department records only")
    
    action_items = models.TextField(blank=True, help_text="Next steps or assignments for the student")
    
    recorded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-recorded_at']

    def __str__(self):
        return f"Record for Booking #{self.booking_id} ({self.get_attendance_display()})"
