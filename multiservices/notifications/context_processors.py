from .models import Notification


def notification_badge(request):
    if not request.user.is_authenticated:
        return {'has_unread_notifications': False}

    has_unread = (
        Notification.objects.filter(user=request.user, is_read=False).exists()
        or Notification.objects.filter(provider=request.user, is_read=False).exists()
    )
    return {'has_unread_notifications': has_unread}
