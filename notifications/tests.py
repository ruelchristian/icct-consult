import datetime
from django.test import TestCase, Client
from django.core import mail
from accounts.models import User
from directory.models import Department, Category, FacultyProfile, StudentProfile
from bookings.models import Booking
from notifications.models import Notification
from notifications.services import create_and_send_notification, generate_ics_calendar

class PWATests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_manifest_endpoint(self):
        response = self.client.get('/manifest.json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('application/manifest+json', response['Content-Type'])
        self.assertIn('ICCT Consult', response.content.decode())

    def test_service_worker_endpoint(self):
        response = self.client.get('/sw.js')
        self.assertEqual(response.status_code, 200)
        self.assertIn('application/javascript', response['Content-Type'])
        self.assertEqual(response['Service-Worker-Allowed'], '/')
        self.assertIn('icct-consult', response.content.decode())

    def test_offline_fallback_endpoint(self):
        response = self.client.get('/offline/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('You are currently offline', response.content.decode())

class NotificationAndEmailTests(TestCase):
    def setUp(self):
        self.dept = Department.objects.create(code="CCS", name="College of Computer Studies")
        self.category = Category.objects.create(name="Capstone Advising", default_duration_minutes=30)

        self.faculty_user = User.objects.create_user(
            username="faculty_test",
            email="faculty@icct.edu.ph",
            password="testpass123",
            role=User.Role.FACULTY,
            first_name="Alan",
            last_name="Turing"
        )
        self.faculty_profile = FacultyProfile.objects.create(
            user=self.faculty_user,
            department=self.dept,
            employee_id="EMP-999"
        )

        self.student_user = User.objects.create_user(
            username="student_test",
            email="student@icct.edu.ph",
            password="testpass123",
            role=User.Role.STUDENT,
            first_name="Ada",
            last_name="Lovelace"
        )
        self.student_profile = StudentProfile.objects.create(
            user=self.student_user,
            department=self.dept,
            student_number="2026-99999",
            program="BSIT",
            year_level=3
        )

        self.booking = Booking.objects.create(
            student=self.student_profile,
            faculty=self.faculty_profile,
            category=self.category,
            date=datetime.date.today() + datetime.timedelta(days=2),
            start_time=datetime.time(10, 0),
            end_time=datetime.time(10, 30),
            mode=Booking.Mode.FACE_TO_FACE,
            location_or_link="Room 302",
            status=Booking.Status.CONFIRMED,
            reason="Capstone prototype review"
        )

    def test_unread_badge_endpoint(self):
        client = Client()
        client.login(username="student_test", password="testpass123")

        # 0 unread initially
        res = client.get('/notifications/unread-badge/')
        self.assertEqual(res.status_code, 200)
        self.assertNotIn('badge-xs', res.content.decode())

        # Create unread notification
        Notification.objects.create(
            recipient=self.student_user,
            booking=self.booking,
            title="Booking Confirmed",
            message="Your booking is confirmed",
            notification_type=Notification.NotificationType.BOOKING_CONFIRMED
        )

        res = client.get('/notifications/unread-badge/')
        self.assertEqual(res.status_code, 200)
        self.assertIn('badge-xs', res.content.decode())
        self.assertIn('1', res.content.decode())

    def test_ics_generation(self):
        ics = generate_ics_calendar(self.booking)
        self.assertIsNotNone(ics)
        self.assertIn('BEGIN:VCALENDAR', ics)
        self.assertIn('METHOD:REQUEST', ics)
        self.assertIn('STATUS:CONFIRMED', ics)
        self.assertIn('Room 302', ics)
        self.assertIn('END:VCALENDAR', ics)

    def test_email_dispatch_with_ics(self):
        mail.outbox = []
        notif = create_and_send_notification(
            recipient=self.student_user,
            booking=self.booking,
            title="Consultation Confirmed",
            message="Your consultation is confirmed with Prof. Turing.",
            notification_type=Notification.NotificationType.BOOKING_CONFIRMED
        )
        self.assertIsNotNone(notif)
        self.assertEqual(len(mail.outbox), 1)

        sent_email = mail.outbox[0]
        self.assertEqual(sent_email.to, ['student@icct.edu.ph'])
        self.assertIn('[ICCT Consultations] Consultation Confirmed', sent_email.subject)
        # Check that both HTML and Plain Text were dispatched
        self.assertTrue(len(sent_email.alternatives) > 0)
        self.assertEqual(sent_email.alternatives[0][1], "text/html")
        self.assertIn('ICCT COLLEGES', sent_email.alternatives[0][0])
        # Check .ics attachment
        self.assertEqual(len(sent_email.attachments), 1)
        self.assertEqual(sent_email.attachments[0][0], "consultation.ics")
