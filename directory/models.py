from django.db import models
from django.conf import settings

class Department(models.Model):
    name = models.CharField(max_length=150, unique=True)
    code = models.CharField(max_length=20, unique=True, help_text="e.g. CCS, CBA, CAS")
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    default_duration_minutes = models.PositiveIntegerField(default=30)
    is_private = models.BooleanField(default=False, help_text="Confidential consultation type")
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.default_duration_minutes}m)"

class FacultyProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='faculty_profile')
    employee_id = models.CharField(max_length=50, unique=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='faculty_members')
    title = models.CharField(max_length=100, blank=True, help_text="e.g. Instructor, Assistant Professor")
    office_location = models.CharField(max_length=150, blank=True, help_text="e.g. Faculty Room, 3rd Floor Bldg A")
    consultation_room_link = models.URLField(blank=True, help_text="Google Meet or Zoom room link")
    bio = models.TextField(blank=True)

    class Meta:
        ordering = ['user__last_name', 'user__first_name']

    def __str__(self):
        dept_str = f" [{self.department.code}]" if self.department else ""
        return f"{self.user.get_full_name() or self.user.username}{dept_str}"

class StudentProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='student_profile')
    student_number = models.CharField(max_length=50, unique=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='students')
    program = models.CharField(max_length=150, blank=True, help_text="e.g. BS Information Technology")
    year_level = models.PositiveSmallIntegerField(default=1)
    section = models.CharField(max_length=50, blank=True)

    class Meta:
        ordering = ['student_number']

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.student_number})"
