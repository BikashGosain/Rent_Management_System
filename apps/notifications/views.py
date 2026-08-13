from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Notification


@login_required
def notification_list(request):
    filter_type = request.GET.get("filter", "all")
    notifications = Notification.objects.filter(recipient=request.user)

    if filter_type == "unread":
        notifications = notifications.filter(is_read=False)
    elif filter_type == "read":
        notifications = notifications.filter(is_read=True)

    unread_count = Notification.objects.filter(
        recipient=request.user, is_read=False
    ).count()
    read_count = Notification.objects.filter(
        recipient=request.user, is_read=True
    ).count()
    total_count = Notification.objects.filter(recipient=request.user).count()

    return render(
        request,
        "notifications/notification_list.html",
        {
            "notifications": notifications,
            "filter_type": filter_type,
            "unread_count": unread_count,
            "read_count": read_count,
            "total_count": total_count,
        },
    )


@login_required
def mark_read(request, pk):
    notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
    notification.mark_read()
    if notification.link:
        return redirect(notification.link)
    return redirect("notifications:list")


@login_required
def mark_single_read(request, pk):
    """Mark single notification as read without redirecting to link."""
    if request.method == "POST":
        notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
        notification.mark_read()
        messages.success(request, "Notification marked as read.")
    return redirect(request.META.get("HTTP_REFERER", "notifications:list"))


@login_required
def mark_all_read(request):
    if request.method == "POST":
        Notification.objects.filter(recipient=request.user, is_read=False).update(
            is_read=True
        )
        messages.success(request, "All notifications marked as read.")
    return redirect("notifications:list")


@login_required
def delete_single(request, pk):
    """Delete a single notification."""
    if request.method == "POST":
        notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
        notification.delete()
        messages.success(request, "Notification deleted.")
    return redirect(request.META.get("HTTP_REFERER", "notifications:list"))


@login_required
def delete_all(request):
    """Delete all notifications."""
    if request.method == "POST":
        filter_type = request.POST.get("filter_type", "all")
        notifications = Notification.objects.filter(recipient=request.user)
        if filter_type == "read":
            notifications = notifications.filter(is_read=True)
        elif filter_type == "unread":
            notifications = notifications.filter(is_read=False)
        count = notifications.count()
        notifications.delete()
        messages.success(request, f"{count} notification(s) deleted.")
    return redirect("notifications:list")


@login_required
def unread_count(request):
    count = Notification.objects.filter(recipient=request.user, is_read=False).count()
    return JsonResponse({"count": count})
