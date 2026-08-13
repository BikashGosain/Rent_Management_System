from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import timedelta
import random
import string


class User(AbstractUser):
    ROLE_CHOICES = [
        ("owner", "House Owner"),
        ("tenant", "Tenant"),
        ("admin", "Admin"),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    phone = models.CharField(max_length=20, blank=True)
    photo = models.ImageField(upload_to="profile_photos/", null=True, blank=True)
    address = models.TextField(blank=True)
    bio = models.TextField(blank=True)
    is_verified = models.BooleanField(default=False)  # ← email/phone OTP verified
    is_google = models.BooleanField(default=False)  # ← signed up via Google

    def is_owner(self):
        return self.role == "owner"

    def is_tenant(self):
        return self.role == "tenant"

    def is_admin(self):
        return self.role == "admin" or self.is_superuser

    def __str__(self):
        return f"{self.username} ({self.role})"


class OTP(models.Model):
    OTP_PURPOSE = [
        ("register", "Registration Verification"),
        ("forgot_password", "Forgot Password"),
        ("login", "Login OTP"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="otps")
    code = models.CharField(max_length=6)
    purpose = models.CharField(max_length=20, choices=OTP_PURPOSE)
    is_used = models.BooleanField(default=False)
    attempts = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    sent_email = models.BooleanField(default=False)
    sent_sms = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"OTP({self.user.username}, {self.purpose}, {self.code})"

    def is_expired(self):
        return timezone.now() > self.expires_at

    def is_valid(self):
        return not self.is_used and not self.is_expired() and self.attempts < 3

    @classmethod
    def generate(cls, user, purpose):
        # Invalidate old OTPs for same purpose
        cls.objects.filter(user=user, purpose=purpose, is_used=False).update(
            is_used=True
        )
        code = "".join(random.choices(string.digits, k=6))
        otp = cls.objects.create(
            user=user,
            code=code,
            purpose=purpose,
            expires_at=timezone.now() + timedelta(minutes=5),
        )
        return otp

    def can_resend(self):
        from django.conf import settings

        wait = getattr(settings, "OTP_RESEND_WAIT", 60)
        return (timezone.now() - self.created_at).seconds >= wait

    def seconds_until_resend(self):
        from django.conf import settings

        wait = getattr(settings, "OTP_RESEND_WAIT", 60)
        elapsed = (timezone.now() - self.created_at).seconds
        return max(0, wait - elapsed)
