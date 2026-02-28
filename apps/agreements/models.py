from django.db import models
from django.contrib.auth import get_user_model
from apps.properties.models import Property, Room
from apps.bookings.models import Booking
from apps.core.models import SoftDeleteModel

User = get_user_model()


class Agreement(SoftDeleteModel):

    STATUS_CHOICES = [
        ('pending_owner',   'Pending Owner Signature'),
        ('pending_tenant',  'Pending Tenant Signature'),
        ('active',          'Active'),
        ('expired',         'Expired'),
        ('terminated',      'Terminated'),
    ]

    # Parties
    owner  = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owner_agreements')
    tenant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tenant_agreements')

    # What is being rented
    property = models.ForeignKey(Property, on_delete=models.SET_NULL, null=True, blank=True, related_name='agreements')
    room     = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, blank=True, related_name='agreements')
    booking = models.ForeignKey(Booking, on_delete=models.SET_NULL, null=True, blank=True, related_name='agreements')

    # Dates
    start_date = models.DateField()
    end_date   = models.DateField()

    # Financial
    rent_amount      = models.DecimalField(max_digits=10, decimal_places=2)
    security_deposit = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    advance_amount   = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Terms
    notice_period_days = models.PositiveIntegerField(default=30, help_text='Notice period in days')
    terms_conditions   = models.TextField(help_text='Terms and conditions of the agreement')

    # Document
    document = models.FileField(upload_to='agreements/', null=True, blank=True, help_text='Upload signed agreement PDF')

    # Digital signatures
    owner_signed    = models.BooleanField(default=False)
    tenant_signed   = models.BooleanField(default=False)
    owner_signed_at  = models.DateTimeField(null=True, blank=True)
    tenant_signed_at = models.DateTimeField(null=True, blank=True)

    # Add these fields to Agreement model
    terminated_by   = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='terminated_agreements')
    terminated_at   = models.DateTimeField(null=True, blank=True)
    termination_reason = models.TextField(blank=True)

    # Status
    status = models.CharField(max_length=20, 
    choices=STATUS_CHOICES, default='pending_owner')

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        target = self.room if self.room else self.property
        return f'Agreement — {self.tenant.username} @ {target} [{self.status}]'

    def get_target_name(self):
        if self.room:
            return f'Room {self.room.room_number} — {self.room.property.title}'
        return self.property.title if self.property else 'N/A'

    def is_active(self):
        return self.status == 'active'

    def is_fully_signed(self):
        return self.owner_signed and self.tenant_signed

    def duration_months(self):
        delta = (self.end_date.year - self.start_date.year) * 12 + \
                (self.end_date.month - self.start_date.month)
        return delta