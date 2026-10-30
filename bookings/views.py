import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.http import HttpResponse, HttpResponseForbidden
from django.utils import timezone
from .models import Booking
from .forms import BookingCreateForm, ActionReasonForm
from .services import create_booking, update_booking_status, get_available_slots_for_date
from directory.models import FacultyProfile, StudentProfile
from availability.models import AvailabilitySlot

def get_faculty_schedule_info(faculty):
    """
    Helper returning active slots, active day numbers, day names,
    faculty format capabilities, and upcoming available dates for the next 14 days.
    """
    active_slots = faculty.availability_slots.filter(is_active=True).order_by('day_of_week', 'start_time')
    day_indices = list(dict.fromkeys(active_slots.values_list('day_of_week', flat=True)))
    
    day_names_map = {
        0: 'Monday',
        1: 'Tuesday',
        2: 'Wednesday',
        3: 'Thursday',
        4: 'Friday',
        5: 'Saturday',
        6: 'Sunday',
    }
    faculty_days_names = [day_names_map[d] for d in day_indices if d in day_names_map]

    # Map each day_of_week to the set of modes available
    day_modes_map = {}
    for slot in active_slots:
        day_modes_map.setdefault(slot.day_of_week, set()).add(slot.mode)

    all_modes = set(active_slots.values_list('mode', flat=True))
    faculty_has_online = (
        AvailabilitySlot.Mode.ONLINE in all_modes or 
        AvailabilitySlot.Mode.HYBRID in all_modes
    )
    faculty_has_f2f = (
        AvailabilitySlot.Mode.FACE_TO_FACE in all_modes or 
        AvailabilitySlot.Mode.HYBRID in all_modes
    )

    today = timezone.localdate()
    upcoming_dates = []
    for offset in range(1, 15):
        d = today + datetime.timedelta(days=offset)
        w = d.weekday()
        if w in day_indices:
            modes = day_modes_map.get(w, set())
            has_online = AvailabilitySlot.Mode.ONLINE in modes or AvailabilitySlot.Mode.HYBRID in modes
            has_f2f = AvailabilitySlot.Mode.FACE_TO_FACE in modes or AvailabilitySlot.Mode.HYBRID in modes
            if has_online and has_f2f:
                mode_label = "F2F & Virtual"
                badge_class = "badge-ghost"
            elif has_online:
                mode_label = "Virtual"
                badge_class = "badge-info text-white"
            else:
                mode_label = "In-Person"
                badge_class = "badge-secondary text-icct-navy"

            upcoming_dates.append({
                'date': d,
                'date_str': d.strftime('%Y-%m-%d'),
                'day_name': d.strftime('%a'),
                'short_str': d.strftime('%b %d'),
                'has_online': has_online,
                'has_f2f': has_f2f,
                'mode_label': mode_label,
                'badge_class': badge_class,
            })

    initial_date = upcoming_dates[0]['date'] if upcoming_dates else (today + datetime.timedelta(days=1))

    return {
        'faculty_slots': active_slots,
        'day_indices': day_indices,
        'faculty_days_names': faculty_days_names,
        'upcoming_dates': upcoming_dates,
        'initial_date': initial_date,
        'faculty_has_online': faculty_has_online,
        'faculty_has_f2f': faculty_has_f2f,
    }

@login_required
def book_faculty_view(request, faculty_id):
    """
    Student booking interface for selecting consultation date, slot, and reason.
    """
    if not request.user.is_student and not request.user.is_department_admin:
        messages.error(request, "Only students can request consultations.")
        return redirect('directory:faculty_detail', faculty_id=faculty_id)

    student = getattr(request.user, 'student_profile', None)
    if not student:
        messages.error(request, "Student profile required to book consultations.")
        return redirect('directory:faculty_list')

    faculty = get_object_or_404(FacultyProfile.objects.select_related('user', 'department'), id=faculty_id)
    schedule_info = get_faculty_schedule_info(faculty)

    if request.method == 'POST':
        form = BookingCreateForm(request.POST)
        if form.is_valid():
            try:
                date = form.cleaned_data['date']
                slot_raw = form.cleaned_data['time_slot']
                start_str, end_str = slot_raw.split('-')
                start_time = datetime.datetime.strptime(start_str.strip(), '%H:%M').time()
                end_time = datetime.datetime.strptime(end_str.strip(), '%H:%M').time()

                booking = create_booking(
                    student=student,
                    faculty=faculty,
                    category=form.cleaned_data['category'],
                    date=date,
                    start_time=start_time,
                    end_time=end_time,
                    mode=form.cleaned_data['mode'],
                    reason=form.cleaned_data['reason'],
                )
                messages.success(request, f"Your consultation request for {date.strftime('%B %d, %Y')} has been submitted to Prof. {faculty.user.get_full_name()}!")
                return redirect('bookings:student_bookings')

            except ValidationError as e:
                form.add_error(None, e.message)
    else:
        form = BookingCreateForm(initial={'date': schedule_info['initial_date']})

    today = timezone.localdate()
    today_str = today.strftime('%Y-%m-%d')
    max_date_str = (today + datetime.timedelta(days=14)).strftime('%Y-%m-%d')
    initial_date_str = schedule_info['initial_date'].strftime('%Y-%m-%d')
    active_bookings_count = Booking.objects.filter(
        student=student,
        status__in=[Booking.Status.PENDING, Booking.Status.CONFIRMED],
        date__gte=today
    ).count() if student else 0

    return render(request, 'bookings/book_slot.html', {
        'faculty': faculty,
        'form': form,
        'today_str': today_str,
        'max_date_str': max_date_str,
        'initial_date_str': initial_date_str,
        'faculty_slots': schedule_info['faculty_slots'],
        'faculty_days_names': schedule_info['faculty_days_names'],
        'upcoming_dates': schedule_info['upcoming_dates'],
        'faculty_has_online': schedule_info['faculty_has_online'],
        'faculty_has_f2f': schedule_info['faculty_has_f2f'],
        'active_bookings_count': active_bookings_count,
        'max_active_bookings': 2,
    })

@login_required
def htmx_get_slots(request, faculty_id):
    """
    htmx fragment loader: Returns available slots for a picked date.
    """
    faculty = get_object_or_404(FacultyProfile, id=faculty_id)
    date_str = request.GET.get('date', '').strip()

    if not date_str:
        return HttpResponse("<p class='text-sm text-base-content/60'>Please pick a date first.</p>")

    try:
        query_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return HttpResponse("<p class='text-sm text-error'>Invalid date selected.</p>")

    today = timezone.localdate()
    if query_date < today:
        return HttpResponse("<div class='alert alert-warning text-sm'>Cannot book consultation dates in the past.</div>")

    schedule_info = get_faculty_schedule_info(faculty)
    slots = get_available_slots_for_date(faculty, query_date)

    return render(request, 'bookings/partials/slot_picker.html', {
        'slots': slots,
        'query_date': query_date,
        'faculty': faculty,
        'faculty_days_names': schedule_info['faculty_days_names'],
        'upcoming_dates': schedule_info['upcoming_dates'],
        'faculty_has_online': schedule_info['faculty_has_online'],
        'faculty_has_f2f': schedule_info['faculty_has_f2f'],
    })

@login_required
def student_bookings_view(request):
    """
    Displays the authenticated student's consultations and history.
    Strictly isolated: students cannot view other students' records.
    """
    student = getattr(request.user, 'student_profile', None)
    if not student:
        messages.error(request, "Access restricted to student accounts.")
        return redirect('core:home')

    status_filter = request.GET.get('status', '').strip()
    bookings_qs = Booking.objects.filter(student=student).select_related('faculty__user', 'category', 'session_record')

    if status_filter:
        bookings_qs = bookings_qs.filter(status=status_filter)

    return render(request, 'bookings/student_bookings.html', {
        'bookings': bookings_qs,
        'status_filter': status_filter,
        'statuses': Booking.Status.choices,
    })

@login_required
def faculty_bookings_view(request):
    """
    Displays the authenticated faculty member's consultations.
    Filtered by ownership: faculty can only view their own consultations.
    """
    faculty = getattr(request.user, 'faculty_profile', None)
    if not faculty and not request.user.is_department_admin:
        messages.error(request, "Access restricted to faculty accounts.")
        return redirect('core:home')

    status_filter = request.GET.get('status', '').strip()
    bookings_qs = Booking.objects.filter(faculty=faculty).select_related('student__user', 'category', 'session_record')

    if status_filter:
        bookings_qs = bookings_qs.filter(status=status_filter)

    return render(request, 'bookings/faculty_bookings.html', {
        'bookings': bookings_qs,
        'status_filter': status_filter,
        'statuses': Booking.Status.choices,
    })

@login_required
def booking_detail_view(request, booking_id):
    """
    Detailed consultation view. Ensures strict access control.
    """
    booking = get_object_or_404(Booking.objects.select_related('student__user', 'faculty__user', 'category', 'session_record'), id=booking_id)

    is_student = hasattr(request.user, 'student_profile') and request.user.student_profile == booking.student
    is_faculty = hasattr(request.user, 'faculty_profile') and request.user.faculty_profile == booking.faculty
    is_admin = request.user.is_department_admin

    if not (is_student or is_faculty or is_admin):
        return HttpResponseForbidden("You do not have permission to view this consultation record.")

    action_form = ActionReasonForm()

    return render(request, 'bookings/booking_detail.html', {
        'booking': booking,
        'is_student': is_student,
        'is_faculty': is_faculty,
        'is_admin': is_admin,
        'action_form': action_form,
    })

@login_required
def booking_action_view(request, booking_id):
    """
    Executes a status transition (Confirm, Decline, Cancel).
    """
    if request.method != 'POST':
        return redirect('bookings:booking_detail', booking_id=booking_id)

    booking = get_object_or_404(Booking, id=booking_id)
    action = request.POST.get('action', '').upper()
    reason = request.POST.get('reason', '').strip()

    status_map = {
        'CONFIRM': Booking.Status.CONFIRMED,
        'DECLINE': Booking.Status.DECLINED,
        'CANCEL': Booking.Status.CANCELLED,
    }

    target_status = status_map.get(action)
    if not target_status:
        messages.error(request, "Unrecognized booking action.")
        return redirect('bookings:booking_detail', booking_id=booking_id)

    try:
        update_booking_status(booking.id, target_status, request.user, reason=reason)
        messages.success(request, f"Booking status updated to {target_status}.")
    except ValidationError as e:
        messages.error(request, str(e))

    return redirect('bookings:booking_detail', booking_id=booking_id)
