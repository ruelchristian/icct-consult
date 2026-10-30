import datetime
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Booking
from availability.models import AvailabilitySlot
from notifications.services import create_and_send_notification
from notifications.models import Notification

MAX_ACTIVE_BOOKINGS_PER_STUDENT = 2

def check_slot_conflict(faculty, date, start_time, end_time, exclude_booking_id=None):
    """
    Checks if an active booking (PENDING or CONFIRMED) already exists
    overlapping the requested time slot.
    Uses select_for_update inside transactions to lock conflicting rows.
    """
    qs = Booking.objects.select_for_update().filter(
        faculty=faculty,
        date=date,
        status__in=[Booking.Status.PENDING, Booking.Status.CONFIRMED],
        start_time__lt=end_time,
        end_time__gt=start_time,
    )
    if exclude_booking_id:
        qs = qs.exclude(id=exclude_booking_id)
    return qs.exists()

def get_available_slots_for_date(faculty, query_date):
    """
    Calculates open consultation slots for a faculty member on a given date
    based on their weekly availability schedule minus booked/pending slots.
    """
    weekday = query_date.weekday()  # 0=Monday .. 6=Sunday
    # Availability slots active for this weekday
    schedules = AvailabilitySlot.objects.filter(
        faculty=faculty,
        day_of_week=weekday,
        is_active=True
    )

    # Active bookings on that day
    existing_bookings = Booking.objects.filter(
        faculty=faculty,
        date=query_date,
        status__in=[Booking.Status.PENDING, Booking.Status.CONFIRMED]
    )

    available_slots = []

    for schedule in schedules:
        duration_minutes = schedule.slot_duration_minutes or 30
        curr_start = schedule.start_time

        # Generate individual slot blocks within the schedule window
        while True:
            # Calculate end time of block
            dummy_dt = datetime.datetime.combine(query_date, curr_start)
            next_dt = dummy_dt + datetime.timedelta(minutes=duration_minutes)
            curr_end = next_dt.time()

            # If past the schedule end time, break
            if curr_end > schedule.end_time and next_dt.date() == dummy_dt.date():
                break

            # Check if this slot conflicts with an existing booking
            is_booked = existing_bookings.filter(
                start_time__lt=curr_end,
                end_time__gt=curr_start
            ).exists()

            slot_data = {
                'start_time': curr_start,
                'end_time': curr_end,
                'mode': schedule.mode,
                'location_or_link': schedule.location_or_link,
                'is_available': not is_booked,
            }
            available_slots.append(slot_data)

            # Move to next block
            curr_start = curr_end
            if curr_start >= schedule.end_time:
                break

    return available_slots

@transaction.atomic
def create_booking(student, faculty, category, date, start_time, end_time, mode=None, location_or_link=None, reason=""):
    """
    Atomically creates a booking request after validating limits and slot availability.
    """
    # 1. Enforce student max active bookings limit (only upcoming pending or confirmed count)
    today = timezone.localdate()
    active_count = Booking.objects.filter(
        student=student,
        status__in=[Booking.Status.PENDING, Booking.Status.CONFIRMED],
        date__gte=today
    ).count()

    if active_count >= MAX_ACTIVE_BOOKINGS_PER_STUDENT:
        raise ValidationError(
            f"You already have {active_count} active bookings. Maximum allowed is {MAX_ACTIVE_BOOKINGS_PER_STUDENT}."
        )

    # 2. Date validation: must be today or future
    if date < today:
        raise ValidationError("Cannot book consultations in the past.")

    # 3. Check slot overlap with lock
    if check_slot_conflict(faculty, date, start_time, end_time):
        raise ValidationError("This consultation slot has already been taken or has a pending request.")

    # 4. Enforce mode and location according to the professor's published slot schedule
    weekday = date.weekday()
    schedule_slot = AvailabilitySlot.objects.filter(
        faculty=faculty,
        day_of_week=weekday,
        start_time__lte=start_time,
        end_time__gte=end_time,
        is_active=True
    ).first()

    if schedule_slot:
        if schedule_slot.mode == AvailabilitySlot.Mode.ONLINE:
            mode = Booking.Mode.ONLINE
            location_or_link = schedule_slot.location_or_link or faculty.consultation_room_link
        elif schedule_slot.mode == AvailabilitySlot.Mode.FACE_TO_FACE:
            mode = Booking.Mode.FACE_TO_FACE
            location_or_link = schedule_slot.location_or_link or faculty.office_location or "Department Faculty Office"
        elif schedule_slot.mode == AvailabilitySlot.Mode.HYBRID:
            if not mode:
                mode = Booking.Mode.FACE_TO_FACE
            location_or_link = schedule_slot.location_or_link if mode == Booking.Mode.ONLINE else (faculty.office_location or "Department Faculty Office")
    else:
        if not mode:
            mode = Booking.Mode.FACE_TO_FACE
        if not location_or_link:
            location_or_link = faculty.office_location if mode == Booking.Mode.FACE_TO_FACE else faculty.consultation_room_link

    # 5. Create booking in PENDING state
    booking = Booking.objects.create(
        student=student,
        faculty=faculty,
        category=category,
        date=date,
        start_time=start_time,
        end_time=end_time,
        mode=mode,
        location_or_link=location_or_link,
        status=Booking.Status.PENDING,
        reason=reason
    )

    # 6. Notify faculty of new booking request
    student_name = student.user.get_full_name() or student.user.username
    time_str = f"{date.strftime('%B %d, %Y')} from {start_time.strftime('%I:%M %p')} to {end_time.strftime('%I:%M %p')}"
    
    create_and_send_notification(
        recipient=faculty.user,
        booking=booking,
        title=f"New Consultation Request from {student_name}",
        message=f"Student {student_name} requested a consultation for {category.name} on {time_str}.\nReason: {reason}",
        notification_type=Notification.NotificationType.BOOKING_REQUEST
    )

    # 7. Notify student confirming request submission receipt
    faculty_name = faculty.user.get_full_name() or faculty.user.username
    create_and_send_notification(
        recipient=student.user,
        booking=booking,
        title="Consultation Request Submitted",
        message=f"Your consultation request with Prof. {faculty_name} for {category.name} on {time_str} has been submitted and is pending review.",
        notification_type=Notification.NotificationType.BOOKING_REQUEST
    )

    return booking

@transaction.atomic
def update_booking_status(booking_id, new_status, actor_user, reason=""):
    """
    Updates the booking status conforming to the allowed state machine transitions.
    """
    booking = Booking.objects.select_for_update().get(id=booking_id)

    # Permission check: Actor must be related or admin
    is_student = hasattr(actor_user, 'student_profile') and actor_user.student_profile == booking.student
    is_faculty = hasattr(actor_user, 'faculty_profile') and actor_user.faculty_profile == booking.faculty
    is_admin = actor_user.is_department_admin

    if not (is_student or is_faculty or is_admin):
        raise ValidationError("You do not have permission to modify this booking.")

    # Valid transitions logic
    current = booking.status

    if current == Booking.Status.PENDING:
        if new_status == Booking.Status.CONFIRMED:
            if not (is_faculty or is_admin):
                raise ValidationError("Only faculty can confirm a booking request.")
            booking.status = Booking.Status.CONFIRMED
            # Notify student
            create_and_send_notification(
                recipient=booking.student.user,
                booking=booking,
                title="Consultation Request Confirmed",
                message=f"Your consultation with Prof. {booking.faculty.user.get_full_name()} on {booking.date} at {booking.start_time.strftime('%I:%M %p')} is confirmed.",
                notification_type=Notification.NotificationType.BOOKING_CONFIRMED
            )

        elif new_status == Booking.Status.DECLINED:
            if not (is_faculty or is_admin):
                raise ValidationError("Only faculty can decline a booking request.")
            booking.status = Booking.Status.DECLINED
            booking.declined_reason = reason
            # Notify student
            create_and_send_notification(
                recipient=booking.student.user,
                booking=booking,
                title="Consultation Request Declined",
                message=f"Your consultation with Prof. {booking.faculty.user.get_full_name()} was declined.\nReason: {reason or 'Schedule conflict'}",
                notification_type=Notification.NotificationType.BOOKING_DECLINED
            )

        elif new_status == Booking.Status.CANCELLED:
            booking.status = Booking.Status.CANCELLED
            booking.cancellation_reason = reason
            notify_target = booking.faculty.user if is_student else booking.student.user
            canceller = "Student" if is_student else "Faculty"
            create_and_send_notification(
                recipient=notify_target,
                booking=booking,
                title=f"Consultation Request Cancelled by {canceller}",
                message=f"The consultation request scheduled for {booking.date} at {booking.start_time.strftime('%I:%M %p')} was cancelled.",
                notification_type=Notification.NotificationType.BOOKING_CANCELLED
            )
        else:
            raise ValidationError(f"Invalid transition from {current} to {new_status}.")

    elif current == Booking.Status.CONFIRMED:
        if new_status == Booking.Status.COMPLETED:
            if not (is_faculty or is_admin):
                raise ValidationError("Only faculty can mark a session as completed.")
            booking.status = Booking.Status.COMPLETED

        elif new_status == Booking.Status.NO_SHOW:
            if not (is_faculty or is_admin):
                raise ValidationError("Only faculty can mark attendance as no-show.")
            booking.status = Booking.Status.NO_SHOW

        elif new_status == Booking.Status.CANCELLED:
            booking.status = Booking.Status.CANCELLED
            booking.cancellation_reason = reason
            notify_target = booking.faculty.user if is_student else booking.student.user
            canceller = "Student" if is_student else "Faculty"
            create_and_send_notification(
                recipient=notify_target,
                booking=booking,
                title=f"Confirmed Consultation Cancelled by {canceller}",
                message=f"The consultation on {booking.date} at {booking.start_time.strftime('%I:%M %p')} has been cancelled.\nReason: {reason}",
                notification_type=Notification.NotificationType.BOOKING_CANCELLED
            )
        else:
            raise ValidationError(f"Invalid transition from {current} to {new_status}.")
    else:
        raise ValidationError(f"Booking is in terminal state ({current}) and cannot be updated.")

    booking.save()
    return booking
