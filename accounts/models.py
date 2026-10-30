from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    class Role(models.TextChoices):
        STUDENT = 'STUDENT', 'Student'
        FACULTY = 'FACULTY', 'Faculty'
        ADMIN = 'ADMIN', 'Admin / Department Head'

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STUDENT)
    phone_number = models.CharField(max_length=20, blank=True)
    school_id = models.CharField(max_length=50, blank=True, db_index=True, help_text="Student Number or Employee ID")

    class Meta:
        indexes = [
            models.Index(fields=['school_id'], name='user_school_id_idx'),
            models.Index(fields=['email'], name='user_email_idx'),
        ]

    @property
    def is_student(self):
        return self.role == self.Role.STUDENT

    @property
    def is_faculty(self):
        return self.role == self.Role.FACULTY

    @property
    def is_department_admin(self):
        return self.role == self.Role.ADMIN or self.is_superuser

    def __str__(self):
        name = self.get_full_name() or self.username
        return f"{name} ({self.get_role_display()})"
