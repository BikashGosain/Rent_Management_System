from django.db import models

# Create your models here.
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model
from apps.properties.models import Property, Room
from apps.agreements.models import Agreement

User = get_user_model()


class Review(models.Model):
    REVIEW_TYPES = [
        ("property", "Property Review"),
        ("room", "Room Review"),
        ("owner", "Owner Review"),
        ("tenant", "Tenant Review"),
    ]

    # Who is reviewing
    reviewer = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="reviews_given"
    )

    # Who/what is being reviewed
    reviewee = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviews_received",
    )
    property = models.ForeignKey(
        Property,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviews",
    )
    room = models.ForeignKey(
        Room, on_delete=models.SET_NULL, null=True, blank=True, related_name="reviews"
    )

    # Linked agreement (ensures only valid tenants/owners can review)
    agreement = models.ForeignKey(
        Agreement,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviews",
    )

    # Review type
    review_type = models.CharField(max_length=10, choices=REVIEW_TYPES)

    # Review content
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating from 1 to 5",
    )
    title = models.CharField(max_length=200)
    comment = models.TextField()
    photo = models.ImageField(upload_to="reviews/", null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = [
            ["reviewer", "property", "agreement", "review_type"],
            ["reviewer", "room", "agreement", "review_type"],
            ["reviewer", "reviewee", "agreement", "review_type"],
        ]

    def __str__(self):
        return f"{self.reviewer.username} — {self.get_review_type_display()} — {self.rating}★"

    def get_star_range(self):
        return range(1, 6)

    def get_filled_stars(self):
        return range(self.rating)

    def get_empty_stars(self):
        return range(5 - self.rating)
