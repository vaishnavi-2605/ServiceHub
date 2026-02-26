from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .models import Notification


@login_required
def notifications_center(request):
    notifications = Notification.objects.filter(
        user=request.user
    ) | Notification.objects.filter(provider=request.user)

    notifications = notifications.order_by('-created_at')

    unread_only = request.GET.get('tab') == 'unread'
    if unread_only:
        notifications = notifications.filter(is_read=False)

    return render(request, 'notifications/center.html', {
        'notifications': notifications,
        'tab': 'unread' if unread_only else 'all',
    })


@login_required
def mark_notification_read(request, notification_id):
    note = get_object_or_404(Notification, id=notification_id)

    if note.user_id != request.user.id and note.provider_id != request.user.id:
        return redirect('notifications_center')

    note.is_read = True
    note.save(update_fields=['is_read'])
    return redirect('notifications_center')


@login_required
def mark_all_notifications_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    Notification.objects.filter(provider=request.user, is_read=False).update(is_read=True)
    return redirect('notifications_center')


@login_required
def notifications_poll(request):
    try:
        since_id = int(request.GET.get('since_id', '0'))
    except ValueError:
        since_id = 0

    notifications = (
        Notification.objects.filter(user=request.user)
        | Notification.objects.filter(provider=request.user)
    ).filter(id__gt=since_id).order_by('id')[:20]

    items = [
        {
            'id': note.id,
            'message': note.message,
            'booking_id': note.booking_id,
            'created_at': note.created_at.strftime('%d %b %Y %I:%M %p'),
        }
        for note in notifications
    ]

    latest_id = items[-1]['id'] if items else since_id

    return JsonResponse({
        'ok': True,
        'notifications': items,
        'latest_id': latest_id,
    })
