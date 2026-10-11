import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from accounts.models import User
from directory.models import Department, Category, FacultyProfile, StudentProfile
from availability.models import AvailabilitySlot
from bookings.models import Booking
from records.models import SessionRecord

class Command(BaseCommand):
    help = "Seed initial demonstration data for ICCT Faculty Consultation System"

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("Seeding ICCT consultation data...")

        # 1. Departments
        ccs, _ = Department.objects.get_or_create(code="CCS", defaults={"name": "College of Computer Studies", "description": "Information Technology and Computer Science"})
        cba, _ = Department.objects.get_or_create(code="CBA", defaults={"name": "College of Business Administration", "description": "Business Administration and Accountancy"})
        coe, _ = Department.objects.get_or_create(code="COE", defaults={"name": "College of Engineering", "description": "Computer and Electronics Engineering"})
        cas, _ = Department.objects.get_or_create(code="CAS", defaults={"name": "College of Arts and Sciences", "description": "General Education and Liberal Arts"})

        # 2. Categories
        capstone, _ = Category.objects.get_or_create(name="Capstone & Thesis Advising", defaults={"default_duration_minutes": 45, "description": "Project defense preparation and manuscript review", "is_private": False})
        subject_help, _ = Category.objects.get_or_create(name="Subject & Coursework Clarification", defaults={"default_duration_minutes": 30, "description": "Clarifications on lecture topics and lab activities", "is_private": False})
        grades, _ = Category.objects.get_or_create(name="Grade Consultation & Deficiencies", defaults={"default_duration_minutes": 30, "description": "Review of midterm/finals grades and missing requirements", "is_private": True})
        academic_adv, _ = Category.objects.get_or_create(name="Academic Counseling", defaults={"default_duration_minutes": 30, "description": "Study plans and curriculum guidance", "is_private": True})

        # 3. Admin User
        admin_user, created = User.objects.get_or_create(username="admin", defaults={
            "email": "admin@icct.edu.ph",
            "first_name": "Dean",
            "last_name": "Administrator",
            "role": User.Role.ADMIN,
            "school_id": "EMP-001",
            "is_staff": True,
            "is_superuser": True,
        })
        if created or not admin_user.check_password("admin123"):
            admin_user.set_password("admin123")
            admin_user.save()

        # 4. Faculty Users
        # Prof. Alan Turing
        turing_user, _ = User.objects.get_or_create(username="prof_turing", defaults={
            "email": "aturing@icct.edu.ph",
            "first_name": "Alan",
            "last_name": "Turing",
            "role": User.Role.FACULTY,
            "school_id": "EMP-101",
        })
        turing_user.set_password("faculty123")
        turing_user.save()

        turing_profile, _ = FacultyProfile.objects.get_or_create(user=turing_user, defaults={
            "employee_id": "EMP-101",
            "department": ccs,
            "title": "Assistant Professor",
            "office_location": "CCS Faculty Room, 3rd Floor Bldg A",
            "consultation_room_link": "https://meet.google.com/abc-turing-demo",
            "bio": "Specializing in Data Structures, Algorithms, and Software Architecture."
        })

        # Prof. Ada Lovelace
        lovelace_user, _ = User.objects.get_or_create(username="prof_lovelace", defaults={
            "email": "alovelace@icct.edu.ph",
            "first_name": "Ada",
            "last_name": "Lovelace",
            "role": User.Role.FACULTY,
            "school_id": "EMP-102",
        })
        lovelace_user.set_password("faculty123")
        lovelace_user.save()

        lovelace_profile, _ = FacultyProfile.objects.get_or_create(user=lovelace_user, defaults={
            "employee_id": "EMP-102",
            "department": ccs,
            "title": "Associate Professor",
            "office_location": "Research Center, 4th Floor Bldg B",
            "consultation_room_link": "https://meet.google.com/xyz-lovelace-demo",
            "bio": "Specializing in Database Management Systems and Web Engineering."
        })

        # 5. Student Users
        # Juan Dela Cruz
        juan_user, _ = User.objects.get_or_create(username="student_juan", defaults={
            "email": "juan.delacruz@icct.edu.ph",
            "first_name": "Juan",
            "last_name": "Dela Cruz",
            "role": User.Role.STUDENT,
            "school_id": "2026-00101",
        })
        juan_user.set_password("student123")
        juan_user.save()

        juan_profile, _ = StudentProfile.objects.get_or_create(user=juan_user, defaults={
            "student_number": "2026-00101",
            "department": ccs,
            "program": "BS Information Technology",
            "year_level": 3,
            "section": "BSIT-3A"
        })

        # Maria Santos
        maria_user, _ = User.objects.get_or_create(username="student_maria", defaults={
            "email": "maria.santos@icct.edu.ph",
            "first_name": "Maria",
            "last_name": "Santos",
            "role": User.Role.STUDENT,
            "school_id": "2026-00102",
        })
        maria_user.set_password("student123")
        maria_user.save()

        maria_profile, _ = StudentProfile.objects.get_or_create(user=maria_user, defaults={
            "student_number": "2026-00102",
            "department": ccs,
            "program": "BS Computer Science",
            "year_level": 4,
            "section": "BSCS-4A"
        })

        # 6. Weekly Availability Slots
        # Prof. Turing: Mondays & Wednesdays 09:00 AM - 12:00 PM (30 min slots)
        AvailabilitySlot.objects.get_or_create(
            faculty=turing_profile,
            day_of_week=AvailabilitySlot.DayOfWeek.MONDAY,
            start_time=datetime.time(9, 0),
            end_time=datetime.time(12, 0),
            defaults={
                "slot_duration_minutes": 30,
                "mode": AvailabilitySlot.Mode.FACE_TO_FACE,
                "location_or_link": "CCS Faculty Room 302",
                "is_active": True
            }
        )
        AvailabilitySlot.objects.get_or_create(
            faculty=turing_profile,
            day_of_week=AvailabilitySlot.DayOfWeek.WEDNESDAY,
            start_time=datetime.time(13, 0),
            end_time=datetime.time(16, 0),
            defaults={
                "slot_duration_minutes": 30,
                "mode": AvailabilitySlot.Mode.ONLINE,
                "location_or_link": "https://meet.google.com/abc-turing-demo",
                "is_active": True
            }
        )

        # Prof. Lovelace: Tuesdays & Thursdays 13:00 - 16:00
        AvailabilitySlot.objects.get_or_create(
            faculty=lovelace_profile,
            day_of_week=AvailabilitySlot.DayOfWeek.TUESDAY,
            start_time=datetime.time(13, 0),
            end_time=datetime.time(16, 0),
            defaults={
                "slot_duration_minutes": 45,
                "mode": AvailabilitySlot.Mode.HYBRID,
                "location_or_link": "Room 405 / Online Meet",
                "is_active": True
            }
        )

        # 7. Sample Initial Bookings
        today = timezone.localdate()
        next_week = today + datetime.timedelta(days=2)

        # A confirmed booking
        booking_confirmed, _ = Booking.objects.get_or_create(
            student=juan_profile,
            faculty=turing_profile,
            date=next_week,
            start_time=datetime.time(9, 0),
            end_time=datetime.time(9, 30),
            defaults={
                "category": capstone,
                "mode": Booking.Mode.FACE_TO_FACE,
                "location_or_link": "CCS Faculty Room 302",
                "status": Booking.Status.CONFIRMED,
                "reason": "Clarification on Entity-Relationship Diagram and DFD Level 1 for Capstone 1 Defense."
            }
        )

        # A pending request
        Booking.objects.get_or_create(
            student=maria_profile,
            faculty=turing_profile,
            date=next_week,
            start_time=datetime.time(9, 30),
            end_time=datetime.time(10, 0),
            defaults={
                "category": subject_help,
                "mode": Booking.Mode.FACE_TO_FACE,
                "location_or_link": "CCS Faculty Room 302",
                "status": Booking.Status.PENDING,
                "reason": "Midterm laboratory exercise questions on binary search trees."
            }
        )

        # A completed historical booking with session record
        past_date = today - datetime.timedelta(days=3)
        booking_past, _ = Booking.objects.get_or_create(
            student=juan_profile,
            faculty=lovelace_profile,
            date=past_date,
            start_time=datetime.time(13, 0),
            end_time=datetime.time(13, 45),
            defaults={
                "category": capstone,
                "mode": Booking.Mode.ONLINE,
                "location_or_link": "https://meet.google.com/xyz-lovelace-demo",
                "status": Booking.Status.COMPLETED,
                "reason": "Draft review for Chapter 3 methodology."
            }
        )

        SessionRecord.objects.get_or_create(
            booking=booking_past,
            defaults={
                "attendance": SessionRecord.Attendance.ATTENDED,
                "advice_given": "Revised the system architecture diagram. Recommended using PostgreSQL transactional locking for slot state transitions.",
                "action_items": "Submit revised DFD diagrams by Friday. Review questionnaire analysis.",
                "private_notes": "Student demonstrates solid understanding of Django ORM; advised on time management for defense."
            }
        )

        self.stdout.write(self.style.SUCCESS("Demo data successfully populated!"))
        self.stdout.write("Credentials created:")
        self.stdout.write("  Admin:   username='admin'        password='admin123'")
        self.stdout.write("  Faculty: username='prof_turing'  password='faculty123'")
        self.stdout.write("  Faculty: username='prof_lovelace' password='faculty123'")
        self.stdout.write("  Student: username='student_juan' password='student123'")
        self.stdout.write("  Student: username='student_maria' password='student123'")
