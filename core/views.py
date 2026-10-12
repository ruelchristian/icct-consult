from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from bookings.models import Booking
from directory.models import Department, FacultyProfile, StudentProfile, Category
from availability.models import AvailabilitySlot

def home_view(request):
    if not request.user.is_authenticated:
        categories = Category.objects.filter(is_active=True)[:6]
        departments = Department.objects.all()[:4]
        return render(request, 'core/landing.html', {
            'categories': categories,
            'departments': departments,
        })

    user = request.user
    today = timezone.localdate()

    if user.is_student:
        student = getattr(user, 'student_profile', None)
        upcoming_bookings = []
        pending_bookings = []
        recent_records = []
        if student:
            upcoming_bookings = Booking.objects.filter(
                student=student,
                status=Booking.Status.CONFIRMED,
                date__gte=today
            ).select_related('faculty__user', 'category').order_by('date', 'start_time')[:5]

            pending_bookings = Booking.objects.filter(
                student=student,
                status=Booking.Status.PENDING
            ).select_related('faculty__user', 'category').order_by('date', 'start_time')

        return render(request, 'core/dashboard_student.html', {
            'student': student,
            'upcoming_bookings': upcoming_bookings,
            'pending_bookings': pending_bookings,
        })

    elif user.is_faculty:
        faculty = getattr(user, 'faculty_profile', None)
        pending_requests = []
        today_consultations = []
        upcoming_consultations = []
        slots_count = 0
        if faculty:
            pending_requests = Booking.objects.filter(
                faculty=faculty,
                status=Booking.Status.PENDING
            ).select_related('student__user', 'category').order_by('date', 'start_time')

            today_consultations = Booking.objects.filter(
                faculty=faculty,
                date=today,
                status=Booking.Status.CONFIRMED
            ).select_related('student__user', 'category').order_by('start_time')

            upcoming_consultations = Booking.objects.filter(
                faculty=faculty,
                date__gt=today,
                status=Booking.Status.CONFIRMED
            ).select_related('student__user', 'category').order_by('date', 'start_time')[:10]

            slots_count = AvailabilitySlot.objects.filter(faculty=faculty, is_active=True).count()

        return render(request, 'core/dashboard_faculty.html', {
            'faculty': faculty,
            'pending_requests': pending_requests,
            'today_consultations': today_consultations,
            'upcoming_consultations': upcoming_consultations,
            'slots_count': slots_count,
        })

    else:
        # Department Head or Administrator
        total_students = StudentProfile.objects.count()
        total_faculty = FacultyProfile.objects.count()
        total_bookings = Booking.objects.count()
        pending_bookings = Booking.objects.filter(status=Booking.Status.PENDING).count()
        completed_bookings = Booking.objects.filter(status=Booking.Status.COMPLETED).count()
        no_shows = Booking.objects.filter(status=Booking.Status.NO_SHOW).count()
        recent_bookings = Booking.objects.select_related('student__user', 'faculty__user', 'category').order_by('-created_at')[:8]

        return render(request, 'core/dashboard_admin.html', {
            'total_students': total_students,
            'total_faculty': total_faculty,
            'total_bookings': total_bookings,
            'pending_bookings': pending_bookings,
            'completed_bookings': completed_bookings,
            'no_shows': no_shows,
            'recent_bookings': recent_bookings,
        })

def service_worker_view(request):
    """
    Serves the PWA Service Worker from the root origin so its scope covers '/'.
    """
    from django.conf import settings
    from django.http import HttpResponse

    sw_path = settings.BASE_DIR / 'static' / 'js' / 'sw.js'
    try:
        with open(sw_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception:
        content = "// Service worker unavailable"

    response = HttpResponse(content, content_type='application/javascript')
    response['Service-Worker-Allowed'] = '/'
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return response

def manifest_view(request):
    """
    Serves the PWA Web App Manifest.
    """
    from django.conf import settings
    from django.http import HttpResponse

    manifest_path = settings.BASE_DIR / 'static' / 'manifest.json'
    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception:
        content = "{}"

    response = HttpResponse(content, content_type='application/manifest+json')
    response['Cache-Control'] = 'public, max-age=86400'
    return response

def offline_view(request):
    """
    Serves the offline fallback page cached by the service worker.
    """
    return render(request, 'offline.html')
