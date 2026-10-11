from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from bookings.models import Booking
from .models import SessionRecord
from .forms import SessionRecordForm
from notifications.services import create_and_send_notification
from notifications.models import Notification

@login_required
def add_edit_session_record_view(request, booking_id):
    """
    Faculty enters session notes and attendance outcome.
    Changes booking status to COMPLETED or NO_SHOW.
    """
    booking = get_object_or_404(Booking.objects.select_related('faculty', 'student__user'), id=booking_id)

    is_faculty = hasattr(request.user, 'faculty_profile') and request.user.faculty_profile == booking.faculty
    if not is_faculty and not request.user.is_department_admin:
        return HttpResponseForbidden("Only the designated faculty member can document this session.")

    record, created = SessionRecord.objects.get_or_create(booking=booking)

    if request.method == 'POST':
        form = SessionRecordForm(request.POST, instance=record)
        if form.is_valid():
            record = form.save()

            # Synchronize booking status
            if record.attendance == SessionRecord.Attendance.ATTENDED:
                booking.status = Booking.Status.COMPLETED
            else:
                booking.status = Booking.Status.NO_SHOW
            booking.save()

            # Notify student if advice was published
            if record.advice_given:
                create_and_send_notification(
                    recipient=booking.student.user,
                    booking=booking,
                    title="Consultation Advice & Notes Available",
                    message=f"Prof. {booking.faculty.user.get_full_name()} has published advice for your consultation on {booking.date}.",
                    notification_type=Notification.NotificationType.RECORD_ADDED
                )

            messages.success(request, "Session record and attendance saved successfully.")
            return redirect('bookings:booking_detail', booking_id=booking.id)
    else:
        form = SessionRecordForm(instance=record)

    return render(request, 'records/record_form.html', {
        'form': form,
        'booking': booking,
        'record': record,
    })

@login_required
def view_session_record_view(request, booking_id):
    """
    View consultation advice.
    Students see advice and action points, but private notes are strictly redacted.
    Faculty and department admins can view all fields including private notes.
    """
    booking = get_object_or_404(Booking.objects.select_related('student__user', 'faculty__user'), id=booking_id)
    record = get_object_or_404(SessionRecord, booking=booking)

    is_student = hasattr(request.user, 'student_profile') and request.user.student_profile == booking.student
    is_faculty = hasattr(request.user, 'faculty_profile') and request.user.faculty_profile == booking.faculty
    is_admin = request.user.is_department_admin

    if not (is_student or is_faculty or is_admin):
        return HttpResponseForbidden("Access denied.")

    return render(request, 'records/record_detail.html', {
        'booking': booking,
        'record': record,
        'can_view_private_notes': is_faculty or is_admin,
    })
