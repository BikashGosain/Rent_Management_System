from .models import Notification


# def unread_notifications(request):
#     """Makes unread_count available in all templates."""
#     if request.user.is_authenticated:
#         count = Notification.objects.filter(
#             recipient=request.user, is_read=False
#         ).count()
#         return {'unread_notifications_count': count}
#     return {'unread_notifications_count': 0}

def unread_notifications(request):
    """Makes unread_count available in all templates."""

    user = getattr(request, "user", None)

    if user is not None and user.is_authenticated:
        count = Notification.objects.filter(
            recipient=user,
            is_read=False
        ).count()

        return {
            "unread_notifications_count": count
        }

    return {
        "unread_notifications_count": 0
    }