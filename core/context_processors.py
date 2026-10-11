from notifications.models import Notification

def system_context(request):
    """
    Exposes role flags and unread notifications count globally across templates.
    """
    context = {
        'is_student': False,
        'is_faculty': False,
        'is_department_admin': False,
        'unread_notifications_count': 0,
    }

    if request.user.is_authenticated:
        context['is_student'] = request.user.is_student
        context['is_faculty'] = request.user.is_faculty
        context['is_department_admin'] = request.user.is_department_admin
        context['unread_notifications_count'] = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).count()

    return context
