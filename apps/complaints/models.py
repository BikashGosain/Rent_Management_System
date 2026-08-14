from django.db import models
from django.contrib.auth import get_user_model
from apps.properties.models import Property, Room
from apps.agreements.models import Agreement
from apps.core.models import SoftDeleteModel


User = get_user_model()


class Complaint(SoftDeleteModel):
    CATEGORIES = [
        ("maintenance", "Maintenance Issue"),
        ("noise", "Noise Complaint"),
        ("utility", "Water/Electricity Problem"),
        ("security", "Security Issue"),
        ("neighbor", "Neighbor Dispute"),
        ("owner", "Owner Dispute"),
        ("other", "Other"),
    ]

    PRIORITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("urgent", "Urgent"),
    ]

    STATUS_CHOICES = [
        ("open", "Open"),
        ("in_progress", "In Progress"),
        ("resolved", "Resolved"),
        ("closed", "Closed"),
    ]

    SUBMITTED_BY = [
        ("tenant", "Tenant"),
        ("owner", "Owner"),
    ]

    # Who submitted
    tenant = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="complaints"
    )
    owner = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="received_complaints"
    )

    # What it's about
    property = models.ForeignKey(
        Property,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="complaints",
    )
    room = models.ForeignKey(
        Room,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="complaints",
    )
    agreement = models.ForeignKey(
        Agreement,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="complaints",
    )

    # Complaint details
    category = models.CharField(max_length=20, choices=CATEGORIES)
    priority = models.CharField(
        max_length=10, choices=PRIORITY_CHOICES, default="medium"
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    attachment = models.ImageField(upload_to="complaints/", null=True, blank=True)

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="open")

    submitted_by = models.CharField(
        max_length=10, choices=SUBMITTED_BY, default="tenant"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_category_display()} — {self.title} [{self.status}]"

    def get_target_name(self):
        if self.room:
            return f"Room {self.room.room_number} — {self.room.property.title}"
        return self.property.title if self.property else "N/A"

    def is_open(self):
        return self.status == "open"

    def is_resolved(self):
        return self.status in ["resolved", "closed"]


class ComplaintResponse(models.Model):
    complaint = models.ForeignKey(
        Complaint, on_delete=models.CASCADE, related_name="responses"
    )
    responder = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="complaint_responses"
    )
    message = models.TextField()
    attachment = models.ImageField(
        upload_to="complaint_responses/", null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Response by {self.responder.username} on {self.complaint.title}"
