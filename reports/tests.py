from django.test import TestCase
from django.utils import timezone
from accounts.models import User
from directory.models import Department, Category, FacultyProfile, StudentProfile
from bookings.models import Booking
from reports.services import generate_consultation_pdf

class ReportGenerationTests(TestCase):
    def setUp(self):
        dept = Department.objects.create(name="Computer Studies", code="CCS")
        cat = Category.objects.create(name="Advising", default_duration_minutes=30)
        f_user = User.objects.create_user(username="prof_r", password="p", role=User.Role.FACULTY, first_name="Grace", last_name="Hopper")
        faculty = FacultyProfile.objects.create(user=f_user, employee_id="EMP-R1", department=dept)
        s_user = User.objects.create_user(username="stud_r", password="p", role=User.Role.STUDENT, first_name="Juan", last_name="Cruz")
        student = StudentProfile.objects.create(user=s_user, student_number="ST-R1", department=dept)

        Booking.objects.create(
            student=student,
            faculty=faculty,
            category=cat,
            date=timezone.localdate(),
            start_time=timezone.now().time(),
            end_time=(timezone.now() + timezone.timedelta(minutes=30)).time(),
            status=Booking.Status.COMPLETED,
            reason="Sample report booking"
        )

    def test_pdf_report_generates_valid_stream(self):
        qs = Booking.objects.all()
        buffer = generate_consultation_pdf(qs, title="Test Report", department_name="CCS")
        pdf_bytes = buffer.getvalue()
        
        # Check PDF header bytes %PDF-
        self.assertTrue(pdf_bytes.startswith(b'%PDF-'))
        self.assertGreater(len(pdf_bytes), 1000)
