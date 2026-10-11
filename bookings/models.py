from django.db import models
from directory.models import FacultyProfile, StudentProfile, Category

class Booking(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending Approval'
        CONFIRMED = 'CONFIRMED', 'Confirmed'
        DECLINED = 'DECLINED', 'Declined'
        CANCELLED = 'CANCELLED', 'Cancelled'
        COMPLETED = 'COMPLETED', 'Completed'
        NO_SHOW = 'NO_SHOW', 'No-Show'

    class Mode(models.TextChoices):
        FACE_TO_FACE = 'F2F', 'Face-to-Face'
        ONLINE = 'ONLINE', 'Online (Virtual)'

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='bookings')
    faculty = models.ForeignKey(FacultyProfile, on_delete=models.CASCADE, related_name='consultations')
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='bookings')

    date = models.DateField(db_index=True)
    start_time = models.TimeField()
    end_time = models.TimeField()

    mode = models.CharField(max_length=20, choices=Mode.choices, default=Mode.FACE_TO_FACE)
    location_or_link = models.CharField(max_length=255, blank=True)

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)
    reason = models.TextField(help_text="Purpose and concerns for the consultation")
    declined_reason = models.TextField(blank=True, help_text="Reason provided by faculty if declined")
    cancellation_reason = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-start_time']
        indexes = [
            models.Index(fields=['faculty', 'date', 'status']),
            models.Index(fields=['student', 'status']),
            models.Index(fields=['date', 'start_time']),
        ]

    def __str__(self):
        return f"{self.student.user.get_full_name()} with {self.faculty.user.get_full_name()} ({self.date} {self.start_time.strftime('%I:%M %p')}) - {self.get_status_display()}"

    @property
    def is_active(self):
        """Active booking holding a slot."""
        return self.status in [self.Status.PENDING, self.Status.CONFIRMED]

    @property
    def can_cancel(self):
        """Student or faculty can cancel if still pending or confirmed."""
        return self.status in [self.Status.PENDING, self.Status.CONFIRMED]
