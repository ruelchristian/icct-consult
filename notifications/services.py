import logging
from django.core.mail import send_mail
from django.conf import settings
from .models import Notification

logger = logging.getLogger(__name__)

def create_and_send_notification(recipient, booking, title, message, notification_type):
    """
    Creates an in-app Notification record and dispatches an email notification.
    """
    notification = Notification.objects.create(
        recipient=recipient,
        booking=booking,
        title=title,
        message=message,
        notification_type=notification_type
    )

    if recipient.email:
        try:
            send_mail(
                subject=f"[ICCT Consultations] {title}",
                message=f"Hello {recipient.get_full_name() or recipient.username},\n\n{message}\n\n---\nICCT Colleges Consultation & Scheduling System",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient.email],
                fail_silently=True,
            )
        except Exception as e:
            logger.warning(f"Failed to send email to {recipient.email}: {e}")

    return notification
