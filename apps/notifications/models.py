from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ("booking_received", "Booking Request Received"),
        ("booking_accepted", "Booking Accepted"),
        ("booking_rejected", "Booking Rejected"),
        ("agreement_created", "Agreement Created"),
        ("agreement_signed", "Agreement Signed"),
        ("agreement_terminated", "Agreement Terminated"),
        ("payment_due", "Payment Due"),
        ("payment_received", "Payment Received"),
        ("complaint_submitted", "Complaint Submitted"),
        ("complaint_response", "Complaint Response Received"),
    ]

    recipient = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notifications"
    )
    notif_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    link = models.CharField(
        max_length=300, blank=True, help_text="URL to redirect when clicked"
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.notif_type} → {self.recipient.username}"

    def mark_read(self):
        self.is_read = True
        self.save()
