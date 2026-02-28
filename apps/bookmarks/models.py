from django.db import models
from django.contrib.auth import get_user_model
from apps.properties.models import Property, Room

User = get_user_model()


class Bookmark(models.Model):
    user      = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookmarks')
    property  = models.ForeignKey(Property, on_delete=models.CASCADE, null=True, blank=True, related_name='bookmarks')
    room      = models.ForeignKey(Room, on_delete=models.CASCADE, null=True, blank=True, related_name='bookmarks')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = [
            ['user', 'property'],
            ['user', 'room'],
        ]

    def __str__(self):
        if self.room:
            return f'{self.user.username} → Room {self.room.room_number}'
        return f'{self.user.username} → {self.property.title}'

    def get_target_name(self):
        if self.room:
            return f'Room {self.room.room_number} — {self.room.property.title}'
        return self.property.title

    def get_target_type(self):
        return 'room' if self.room else 'property'

    def get_rent_price(self):
        if self.room:
            return self.room.rent_price
        return self.property.rent_price

    def get_city(self):
        if self.room:
            return self.room.property.city
        return self.property.city

    def get_detail_url(self):
        if self.room:
            return f'/properties/{self.room.property.pk}/room/{self.room.pk}/'
        return f'/properties/{self.property.pk}/'