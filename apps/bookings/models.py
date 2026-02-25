from django.db import models
from django.contrib.auth import get_user_model
from apps.properties.models import Property, Room

User = get_user_model()


class Booking(models.Model):

    STATUS_CHOICES = [
        ('pending',   'Pending'),
        ('accepted',  'Accepted'),
        ('rejected',  'Rejected'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]

    # Who is booking
    tenant   = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')

    # What they are booking — either a whole property OR a room
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='bookings', null=True, blank=True)
    room     = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='bookings', null=True, blank=True)

    # Dates
    move_in_date  = models.DateField()
    move_out_date = models.DateField(null=True, blank=True)

    # Optional message
    message = models.TextField(blank=True, help_text='Optional message to the owner')

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Owner response
    owner_note = models.TextField(blank=True, help_text='Note from owner when accepting or rejecting')

    # Timestamps
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        target = self.room if self.room else self.property
        return f'Booking by {self.tenant.username} — {target} [{self.status}]'

    def get_owner(self):
        if self.room:
            return self.room.property.owner
        return self.property.owner

    def get_target(self):
        """Return the room or property being booked."""
        return self.room if self.room else self.property

    def get_target_name(self):
        if self.room:
            return f'Room {self.room.room_number} — {self.room.property.title}'
        return self.property.title

    def get_rent_price(self):
        if self.room:
            return self.room.rent_price
        return self.property.rent_price

    def is_pending(self):
        return self.status == 'pending'

    def is_accepted(self):
        return self.status == 'accepted'