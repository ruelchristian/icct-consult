import datetime
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from accounts.models import User
from directory.models import Department, Category, FacultyProfile, StudentProfile
from availability.models import AvailabilitySlot
from bookings.models import Booking
from bookings.services import create_booking, update_booking_status, check_slot_conflict
from records.models import SessionRecord

class BookingWorkflowTests(TestCase):
    def setUp(self):
        self.dept = Department.objects.create(name="Computer Studies", code="CCS")
        self.category = Category.objects.create(name="Capstone Advising", default_duration_minutes=30)

        # Faculty
        self.f_user = User.objects.create_user(username="prof_test", password="pass", role=User.Role.FACULTY, first_name="Alan", last_name="Turing")
        self.faculty = FacultyProfile.objects.create(user=self.f_user, employee_id="EMP-999", department=self.dept)

        # Students
        self.s1_user = User.objects.create_user(username="s1", password="pass", role=User.Role.STUDENT, first_name="Juan", last_name="Dela Cruz")
        self.student1 = StudentProfile.objects.create(user=self.s1_user, student_number="ST-001", department=self.dept)

        self.s2_user = User.objects.create_user(username="s2", password="pass", role=User.Role.STUDENT, first_name="Maria", last_name="Santos")
        self.student2 = StudentProfile.objects.create(user=self.s2_user, student_number="ST-002", department=self.dept)

        self.tomorrow = timezone.localdate() + datetime.timedelta(days=1)
        self.start_t = datetime.time(9, 0)
        self.end_t = datetime.time(9, 30)

    def test_successful_booking_creation(self):
        booking = create_booking(
            student=self.student1,
            faculty=self.faculty,
            category=self.category,
            date=self.tomorrow,
            start_time=self.start_t,
            end_time=self.end_t,
            reason="Initial thesis topic inquiry"
        )
        self.assertEqual(booking.status, Booking.Status.PENDING)
        self.assertTrue(check_slot_conflict(self.faculty, self.tomorrow, self.start_t, self.end_t))

    def test_double_booking_conflict_prevented(self):
        # Student 1 books 9:00 - 9:30
        create_booking(
            student=self.student1,
            faculty=self.faculty,
            category=self.category,
            date=self.tomorrow,
            start_time=self.start_t,
            end_time=self.end_t,
            reason="First request"
        )

        # Student 2 attempts to book overlapping slot (9:15 - 9:45)
        with self.assertRaises(ValidationError) as ctx:
            create_booking(
                student=self.student2,
                faculty=self.faculty,
                category=self.category,
                date=self.tomorrow,
                start_time=datetime.time(9, 15),
                end_time=datetime.time(9, 45),
                reason="Second request overlapping"
            )
        self.assertIn("already been taken", str(ctx.exception))

    def test_max_active_bookings_limit(self):
        # Create 2 active bookings for student1
        create_booking(
            student=self.student1,
            faculty=self.faculty,
            category=self.category,
            date=self.tomorrow,
            start_time=datetime.time(9, 0),
            end_time=datetime.time(9, 30),
            reason="Booking 1"
        )
        create_booking(
            student=self.student1,
            faculty=self.faculty,
            category=self.category,
            date=self.tomorrow,
            start_time=datetime.time(10, 0),
            end_time=datetime.time(10, 30),
            reason="Booking 2"
        )

        # 3rd active booking should be rejected
        with self.assertRaises(ValidationError) as ctx:
            create_booking(
                student=self.student1,
                faculty=self.faculty,
                category=self.category,
                date=self.tomorrow,
                start_time=datetime.time(11, 0),
                end_time=datetime.time(11, 30),
                reason="Booking 3 (should fail)"
            )
        self.assertIn("Maximum allowed is 2", str(ctx.exception))

    def test_status_transitions(self):
        booking = create_booking(
            student=self.student1,
            faculty=self.faculty,
            category=self.category,
            date=self.tomorrow,
            start_time=self.start_t,
            end_time=self.end_t,
            reason="Status transition test"
        )

        # Faculty confirms
        update_booking_status(booking.id, Booking.Status.CONFIRMED, self.f_user)
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.CONFIRMED)

        # Faculty completes
        update_booking_status(booking.id, Booking.Status.COMPLETED, self.f_user)
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.COMPLETED)

        # Invalid transition: COMPLETED cannot go back to PENDING
        with self.assertRaises(ValidationError):
            update_booking_status(booking.id, Booking.Status.PENDING, self.f_user)
