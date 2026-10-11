from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Notification

@login_required
def notification_list_view(request):
    notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')

    # Optional: mark all as read if requested
    if request.GET.get('read_all') == '1':
        notifications.filter(is_read=False).update(is_read=True)
        return redirect('notifications:list')

    return render(request, 'notifications/notification_list.html', {
        'notifications': notifications,
    })

@login_required
def mark_read_view(request, notif_id):
    notif = get_object_or_404(Notification, id=notif_id, recipient=request.user)
    notif.is_read = True
    notif.save()
    if notif.booking:
        return redirect('bookings:booking_detail', booking_id=notif.booking_id)
    return redirect('notifications:list')
