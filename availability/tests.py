import datetime
from django.test import TestCase
from django.contrib.auth import get_user_model
from directory.models import Department, FacultyProfile
from availability.models import AvailabilitySlot
from availability.forms import AvailabilitySlotForm

User = get_user_model()

class AvailabilityPresetAndValidationTests(TestCase):
    def setUp(self):
        self.dept = Department.objects.create(code="CCS", name="College of Computer Studies")
        self.faculty_user = User.objects.create_user(
            username="prof_test",
            email="test@icct.edu.ph",
            first_name="Prof",
            last_name="Test",
            role=User.Role.FACULTY,
            school_id="EMP-999"
        )
        self.faculty = FacultyProfile.objects.create(
            user=self.faculty_user,
            employee_id="EMP-999",
            department=self.dept
        )

    def test_virtual_mode_requires_valid_link(self):
        # 1. Online without link should fail
        form_empty_link = AvailabilitySlotForm(data={
            'day_of_week': '0',
            'start_time': '09:00',
            'end_time': '12:00',
            'slot_duration_minutes': 30,
            'mode': AvailabilitySlot.Mode.ONLINE,
            'location_or_link': '',
        })
        self.assertFalse(form_empty_link.is_valid())
        self.assertIn('location_or_link', form_empty_link.errors)
        self.assertIn("required when Mode is Online", form_empty_link.errors['location_or_link'][0])

        # 2. Online with invalid link (not starting with http/https) should fail
        form_invalid_url = AvailabilitySlotForm(data={
            'day_of_week': '0',
            'start_time': '09:00',
            'end_time': '12:00',
            'slot_duration_minutes': 30,
            'mode': AvailabilitySlot.Mode.ONLINE,
            'location_or_link': 'Room 302',
        })
        self.assertFalse(form_invalid_url.is_valid())
        self.assertIn('location_or_link', form_invalid_url.errors)
        self.assertIn("valid URL", form_invalid_url.errors['location_or_link'][0])

        # 3. Online with valid Google Meet URL should succeed
        form_valid = AvailabilitySlotForm(data={
            'day_of_week': '0',
            'start_time': '09:00',
            'end_time': '12:00',
            'slot_duration_minutes': 30,
            'mode': AvailabilitySlot.Mode.ONLINE,
            'location_or_link': 'https://meet.google.com/abc-defg-hij',
        })
        self.assertTrue(form_valid.is_valid())

    def test_f2f_mode_allows_empty_or_room_link(self):
        form = AvailabilitySlotForm(data={
            'day_of_week': '1',
            'start_time': '13:00',
            'end_time': '16:00',
            'slot_duration_minutes': 30,
            'mode': AvailabilitySlot.Mode.FACE_TO_FACE,
            'location_or_link': '',
        })
        self.assertTrue(form.is_valid())

    def test_preset_weekdays_creates_five_slots(self):
        form = AvailabilitySlotForm(data={
            'day_of_week': 'WEEKDAYS',
            'start_time': '08:00',
            'end_time': '11:00',
            'slot_duration_minutes': 30,
            'mode': AvailabilitySlot.Mode.FACE_TO_FACE,
            'location_or_link': 'Room 401',
        })
        self.assertTrue(form.is_valid())
        slots = form.save_slots(self.faculty)
        self.assertEqual(len(slots), 5)
        days = [s.day_of_week for s in slots]
        self.assertEqual(days, [0, 1, 2, 3, 4])

    def test_preset_weekends_creates_two_slots(self):
        form = AvailabilitySlotForm(data={
            'day_of_week': 'WEEKENDS',
            'start_time': '13:00',
            'end_time': '17:00',
            'slot_duration_minutes': 45,
            'mode': AvailabilitySlot.Mode.ONLINE,
            'location_or_link': 'https://meet.google.com/weekend-class',
        })
        self.assertTrue(form.is_valid())
        slots = form.save_slots(self.faculty)
        self.assertEqual(len(slots), 2)
        days = [s.day_of_week for s in slots]
        self.assertEqual(days, [5, 6]) # Saturday and Sunday

    def test_sunday_slot_supported(self):
        slot = AvailabilitySlot.objects.create(
            faculty=self.faculty,
            day_of_week=AvailabilitySlot.DayOfWeek.SUNDAY,
            start_time=datetime.time(9, 0),
            end_time=datetime.time(12, 0),
            slot_duration_minutes=30,
            mode=AvailabilitySlot.Mode.FACE_TO_FACE
        )
        self.assertEqual(slot.day_of_week, 6)
        self.assertEqual(slot.get_day_of_week_display(), 'Sunday')
