from django.db import models
from directory.models import FacultyProfile

class AvailabilitySlot(models.Model):
    class DayOfWeek(models.IntegerChoices):
        MONDAY = 0, 'Monday'
        TUESDAY = 1, 'Tuesday'
        WEDNESDAY = 2, 'Wednesday'
        THURSDAY = 3, 'Thursday'
        FRIDAY = 4, 'Friday'
        SATURDAY = 5, 'Saturday'

    class Mode(models.TextChoices):
        FACE_TO_FACE = 'F2F', 'Face-to-Face'
        ONLINE = 'ONLINE', 'Online (Virtual)'
        HYBRID = 'HYBRID', 'Flexible / Hybrid'

    faculty = models.ForeignKey(FacultyProfile, on_delete=models.CASCADE, related_name='availability_slots')
    day_of_week = models.IntegerField(choices=DayOfWeek.choices)
    start_time = models.TimeField()
    end_time = models.TimeField()
    slot_duration_minutes = models.PositiveIntegerField(default=30, help_text="Duration per booking block in minutes")
    mode = models.CharField(max_length=20, choices=Mode.choices, default=Mode.FACE_TO_FACE)
    location_or_link = models.CharField(max_length=255, blank=True, help_text="Office/Room number or Meet URL")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['day_of_week', 'start_time']

    def __str__(self):
        day = self.get_day_of_week_display()
        return f"{self.faculty.user.get_full_name()} | {day} {self.start_time.strftime('%I:%M %p')} - {self.end_time.strftime('%I:%M %p')} ({self.get_mode_display()})"
