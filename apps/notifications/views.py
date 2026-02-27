from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Notification


@login_required
def notification_list(request):
    """Show all notifications for current user."""
    notifications = Notification.objects.filter(recipient=request.user)

    # Mark all as read when page is opened
    notifications.filter(is_read=False).update(is_read=True)

    return render(request, 'notifications/notification_list.html', {
        'notifications': notifications,
    })


@login_required
def mark_read(request, pk):
    """Mark a single notification as read and redirect to its link."""
    notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
    notification.mark_read()
    if notification.link:
        return redirect(notification.link)
    return redirect('notifications:list')


@login_required
def mark_all_read(request):
    """Mark all notifications as read."""
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    return redirect('notifications:list')


@login_required
def unread_count(request):
    """API endpoint — returns unread count as JSON for navbar badge."""
    count = Notification.objects.filter(recipient=request.user, is_read=False).count()
    return JsonResponse({'count': count})