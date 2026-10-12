import logging
import datetime
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.urls import reverse
from .models import Notification

logger = logging.getLogger(__name__)

def generate_ics_calendar(booking):
    """
    Generates an RFC 5545 iCalendar (.ics) string for confirmed consultations.
    Allows students and faculty to add the consultation directly to Google Calendar or Apple/Outlook Calendar.
    """
    try:
        dtstart = datetime.datetime.combine(booking.date, booking.start_time)
        dtend = datetime.datetime.combine(booking.date, booking.end_time)

        # Manila timezone is UTC+8
        tz_offset = datetime.timedelta(hours=8)
        dtstart_utc = (dtstart - tz_offset).strftime('%Y%m%dT%H%M%SZ')
        dtend_utc = (dtend - tz_offset).strftime('%Y%m%dT%H%M%SZ')
        now_utc = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')

        student_name = booking.student.user.get_full_name() or booking.student.user.username
        faculty_name = booking.faculty.user.get_full_name() or booking.faculty.user.username
        summary = f"ICCT Consultation: Prof. {faculty_name} & {student_name}"
        location = booking.location_or_link or "ICCT Colleges"
        desc = f"Topic: {booking.category.name}\\nMode: {booking.get_mode_display()}\\nLocation: {location}\\nReason: {booking.reason}"

        ics = (
            "BEGIN:VCALENDAR\r\n"
            "VERSION:2.0\r\n"
            "PRODID:-//ICCT Colleges//Faculty Consultation System//EN\r\n"
            "CALSCALE:GREGORIAN\r\n"
            "METHOD:REQUEST\r\n"
            "BEGIN:VEVENT\r\n"
            f"UID:consultation-{booking.id}-{now_utc}@icct.edu.ph\r\n"
            f"DTSTAMP:{now_utc}\r\n"
            f"DTSTART:{dtstart_utc}\r\n"
            f"DTEND:{dtend_utc}\r\n"
            f"SUMMARY:{summary}\r\n"
            f"DESCRIPTION:{desc}\r\n"
            f"LOCATION:{location}\r\n"
            "STATUS:CONFIRMED\r\n"
            "END:VEVENT\r\n"
            "END:VCALENDAR\r\n"
        )
        return ics
    except Exception as e:
        logger.warning(f"Error generating .ics calendar for booking {booking.id}: {e}")
        return None

def create_and_send_notification(recipient, booking, title, message, notification_type):
    """
    Creates an in-app Notification record and dispatches a rich HTML/text email.
    If the consultation is confirmed, attaches an .ics calendar invite.
    """
    # 1. In-App Notification Record
    notification = Notification.objects.create(
        recipient=recipient,
        booking=booking,
        title=title,
        message=message,
        notification_type=notification_type
    )

    # 2. Email Notification Dispatch
    if recipient.email:
        try:
            site_url = getattr(settings, 'SITE_URL', 'https://icct-consult.onrender.com').rstrip('/')
            if booking:
                action_url = f"{site_url}{reverse('bookings:booking_detail', kwargs={'booking_id': booking.id})}"
            else:
                action_url = f"{site_url}{reverse('notifications:list')}"

            recipient_name = recipient.get_full_name() or recipient.username

            context = {
                'title': title,
                'message': message,
                'booking': booking,
                'recipient_name': recipient_name,
                'notification_type': notification_type,
                'action_url': action_url,
                'site_url': site_url,
            }

            subject = f"[ICCT Consultations] {title}"
            text_content = render_to_string('emails/notification_email.txt', context)
            html_content = render_to_string('emails/notification_email.html', context)

            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[recipient.email]
            )
            msg.attach_alternative(html_content, "text/html")

            # Attach .ics calendar file if booking confirmed
            if notification_type == Notification.NotificationType.BOOKING_CONFIRMED and booking:
                ics_data = generate_ics_calendar(booking)
                if ics_data:
                    msg.attach(
                        filename="consultation.ics",
                        content=ics_data,
                        mimetype="text/calendar; method=REQUEST; charset=utf-8"
                    )

            msg.send(fail_silently=True)
            logger.info(f"Dispatched consultation notification email to {recipient.email} ({title})")

        except Exception as e:
            logger.warning(f"Failed to send email to {recipient.email}: {e}")

    return notification
