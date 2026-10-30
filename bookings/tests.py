import datetime
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from accounts.models import User
from directory.models import Department, Category, FacultyProfile, StudentProfile
from availability.models import AvailabilitySlot
from bookings.models import Booking
from bookings.services import create_booking, update_booking_status, check_slot_conflict
from django.urls import reverse
from records.models import SessionRecord
from bookings.views import get_faculty_schedule_info

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

    def test_faculty_schedule_info_detects_modes_and_upcoming_dates(self):
        # Add an online slot on Wednesday (2) and an F2F slot on Monday (0)
        AvailabilitySlot.objects.create(
            faculty=self.faculty,
            day_of_week=0, # Monday
            start_time=datetime.time(9, 0),
            end_time=datetime.time(11, 0),
            mode=AvailabilitySlot.Mode.FACE_TO_FACE,
            is_active=True
        )
        AvailabilitySlot.objects.create(
            faculty=self.faculty,
            day_of_week=2, # Wednesday
            start_time=datetime.time(13, 0),
            end_time=datetime.time(15, 0),
            mode=AvailabilitySlot.Mode.ONLINE,
            location_or_link="https://meet.google.com/test-xyz",
            is_active=True
        )

        schedule_info = get_faculty_schedule_info(self.faculty)
        self.assertTrue(schedule_info['faculty_has_online'])
        self.assertTrue(schedule_info['faculty_has_f2f'])
        self.assertIn('Monday', schedule_info['faculty_days_names'])
        self.assertIn('Wednesday', schedule_info['faculty_days_names'])
        self.assertGreater(len(schedule_info['upcoming_dates']), 0)

        # Check upcoming date mode attributes
        for d in schedule_info['upcoming_dates']:
            if d['date'].weekday() == 0:
                self.assertTrue(d['has_f2f'])
                self.assertFalse(d['has_online'])
                self.assertEqual(d['mode_label'], 'In-Person')
            elif d['date'].weekday() == 2:
                self.assertTrue(d['has_online'])
                self.assertFalse(d['has_f2f'])
                self.assertEqual(d['mode_label'], 'Virtual')

    def test_slot_picker_htmx_contains_filter_buttons_and_data_modes(self):
        AvailabilitySlot.objects.create(
            faculty=self.faculty,
            day_of_week=self.tomorrow.weekday(),
            start_time=datetime.time(10, 0),
            end_time=datetime.time(11, 0),
            mode=AvailabilitySlot.Mode.ONLINE,
            location_or_link="https://meet.google.com/test-abc",
            is_active=True
        )
        self.client.force_login(self.s1_user)
        url = reverse('bookings:htmx_slots', kwargs={'faculty_id': self.faculty.id})
        response = self.client.get(f"{url}?date={self.tomorrow.strftime('%Y-%m-%d')}")
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn('slot-filter-ONLINE', content)
        self.assertIn('slot-filter-F2F', content)
        self.assertIn('data-mode="ONLINE"', content)

