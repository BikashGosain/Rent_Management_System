from django.db import models
from django.contrib.auth import get_user_model
from apps.agreements.models import Agreement

User = get_user_model()


class Payment(models.Model):

    PAYMENT_TYPES = [
        ('rent',     'Rent Payment'),
        ('deposit',  'Security Deposit'),
        ('advance',  'Advance Payment'),
        ('penalty',  'Late Fee/Penalty'),
    ]

    PAYMENT_METHODS = [
        ('cash',     'Cash'),
        ('bank',     'Bank Transfer'),
        ('online',   'Online Payment'),
        ('cheque',   'Cheque'),
    ]

    STATUS_CHOICES = [
        ('pending',   'Pending'),
        ('paid',      'Paid'),
        ('overdue',   'Overdue'),
        ('cancelled', 'Cancelled'),
    ]

    # Parties
    agreement = models.ForeignKey(Agreement, on_delete=models.CASCADE, related_name='payments')
    tenant    = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments_made')
    owner     = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments_received')

    # Payment details
    payment_type   = models.CharField(max_length=20, choices=PAYMENT_TYPES, default='rent')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='cash')
    amount         = models.DecimalField(max_digits=10, decimal_places=2)

    # Dates
    due_date  = models.DateField()
    paid_date = models.DateField(null=True, blank=True)

    # For monthly rent tracking
    month = models.PositiveIntegerField(null=True, blank=True, help_text='Month number (1-12)')
    year  = models.PositiveIntegerField(null=True, blank=True, help_text='Year (e.g. 2026)')

    # Extra info
    notes            = models.TextField(blank=True)
    transaction_id   = models.CharField(max_length=100, blank=True, help_text='Bank/online transaction ID')
    receipt          = models.FileField(upload_to='receipts/', null=True, blank=True)

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Auto generated or manual
    is_auto_generated = models.BooleanField(default=False)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-due_date']

    def __str__(self):
        return f'{self.get_payment_type_display()} — {self.tenant.username} — Rs.{self.amount} [{self.status}]'

    def is_paid(self):
        return self.status == 'paid'

    def is_overdue(self):
        from django.utils import timezone
        return self.status == 'pending' and self.due_date < timezone.now().date()

    def get_month_display_name(self):
        if self.month and self.year and 1 <= self.month <= 12:
            import calendar
            return f'{calendar.month_name[self.month]} {self.year}'
        return ''