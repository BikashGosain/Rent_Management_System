from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from apps.properties.models import Property, Room
from apps.core.models import SoftDeleteModel

User = get_user_model()


class Agreement(SoftDeleteModel):

    RENTAL_TYPES = [
        ('fixed',       'Fixed Term'),
        ('month',       'Month-to-Month'),
        ('short',       'Short Term (Daily/Weekly)'),
    ]

    SHORT_TERM_UNIT = [
        ('daily',  'Daily'),
        ('weekly', 'Weekly'),
    ]

    REVIEW_TYPES = [
        ('pending_owner',  'Pending Owner Signature'),
        ('pending_tenant', 'Pending Tenant Signature'),
        ('active',         'Active'),
        ('expired',        'Expired'),
        ('terminated',     'Terminated'),
    ]

    NOTICE_STATUS = [
        ('none',      'No Notice'),
        ('pending',   'Notice Submitted'),
        ('approved',  'Notice Approved'),
        ('rejected',  'Notice Rejected'),
        ('mutual',    'Mutual Agreement'),
    ]

    # Parties
    owner     = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_agreements')
    tenant    = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tenant_agreements')
    property  = models.ForeignKey(Property, on_delete=models.SET_NULL, null=True, blank=True, related_name='agreements')
    room      = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, blank=True, related_name='agreements')
    booking   = models.ForeignKey('bookings.Booking', on_delete=models.SET_NULL, null=True, blank=True, related_name='agreements')

    # Rental type
    rental_type    = models.CharField(max_length=10, choices=RENTAL_TYPES, default='fixed')
    short_term_unit = models.CharField(max_length=10, choices=SHORT_TERM_UNIT, null=True, blank=True)
    short_term_duration = models.PositiveIntegerField(null=True, blank=True, help_text='Number of days or weeks')

    # Dates
    start_date = models.DateField()
    end_date   = models.DateField(null=True, blank=True, help_text='Leave blank for month-to-month')

    # Financial
    rent_amount      = models.DecimalField(max_digits=10, decimal_places=2)
    security_deposit = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    advance_amount   = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Terms
    notice_period_days = models.PositiveIntegerField(default=30)
    terms_conditions   = models.TextField(blank=True)
    document           = models.FileField(upload_to='agreements/', null=True, blank=True)

    # Signatures
    owner_signed     = models.BooleanField(default=False)
    tenant_signed    = models.BooleanField(default=False)
    owner_signed_at  = models.DateTimeField(null=True, blank=True)
    tenant_signed_at = models.DateTimeField(null=True, blank=True)

    # Status
    status = models.CharField(max_length=20, choices=REVIEW_TYPES, default='pending_owner')

    # Termination
    terminated_by      = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='terminated_agreements')
    terminated_at      = models.DateTimeField(null=True, blank=True)
    termination_reason = models.TextField(blank=True)

    # ── Notice System ──────────────────────────────────
    notice_status      = models.CharField(max_length=10, choices=NOTICE_STATUS, default='none')
    notice_given_by    = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='notices_given')
    notice_given_at    = models.DateTimeField(null=True, blank=True)
    notice_vacate_date = models.DateField(null=True, blank=True, help_text='Expected vacate date')
    notice_reason      = models.TextField(blank=True)
    notice_type        = models.CharField(max_length=20, blank=True, choices=[
        ('vacate',      'Notice to Vacate'),
        ('early_term',  'Early Termination Request'),
        ('owner_notice','Owner Notice to Tenant'),
        ('mutual',      'Mutual Termination'),
    ])
    notice_response    = models.TextField(blank=True, help_text='Owner response to notice')
    notice_responded_at = models.DateTimeField(null=True, blank=True)

    # Month-to-month auto renewal
    auto_renew       = models.BooleanField(default=True)
    last_renewed_at  = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Agreement — {self.tenant.username} — {self.get_target_name()}'

    def get_target_name(self):
        if self.room:
            return f'Room {self.room.room_number} — {self.room.property.title}'
        return self.property.title if self.property else 'N/A'

    def is_active(self):
        return self.status == 'active'

    def is_fully_signed(self):
        return self.owner_signed and self.tenant_signed

    def duration_months(self):
        if self.end_date and self.start_date:
            return max(1, (self.end_date.year - self.start_date.year) * 12 +
                       (self.end_date.month - self.start_date.month))
        return None

    def is_month_to_month(self):
        return self.rental_type == 'month'

    def is_short_term(self):
        return self.rental_type == 'short'

    def notice_days_remaining(self):
        """Days remaining in notice period."""
        if self.notice_vacate_date:
            delta = self.notice_vacate_date - timezone.now().date()
            return max(0, delta.days)
        return None

    def notice_progress_percent(self):
        """Progress of notice period as percentage."""
        if self.notice_given_at and self.notice_vacate_date:
            total = (self.notice_vacate_date - self.notice_given_at.date()).days
            elapsed = (timezone.now().date() - self.notice_given_at.date()).days
            if total > 0:
                return min(100, int((elapsed / total) * 100))
        return 0

    def get_rental_type_label(self):
        if self.rental_type == 'fixed':
            return f'Fixed Term ({self.duration_months()} months)'
        elif self.rental_type == 'month':
            return 'Month-to-Month'
        elif self.rental_type == 'short':
            return f'Short Term ({self.short_term_duration} {self.get_short_term_unit_display()})'
        return ''

    def calculate_short_term_end_date(self):
        """Calculate end date for short term rentals."""
        if self.rental_type == 'short' and self.short_term_duration:
            if self.short_term_unit == 'daily':
                return self.start_date + timedelta(days=self.short_term_duration)
            elif self.short_term_unit == 'weekly':
                return self.start_date + timedelta(weeks=self.short_term_duration)
        return None