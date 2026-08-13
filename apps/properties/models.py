from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Property(models.Model):
    PROPERTY_TYPES = [
        ("house", "House"),
        ("apartment", "Apartment"),
        ("villa", "Villa"),
        ("studio", "Studio"),
        ("flat", "Flat"),
        ("shop", "Shop/Commercial"),
        ("office", "Office Space"),
        ("warehouse", "Warehouse"),
        ("other", "Other"),
    ]

    RENT_TYPES = [
        ("whole", "Whole Property"),
        ("rooms", "Individual Rooms"),
    ]

    STATUS_CHOICES = [
        ("available", "Available"),
        ("occupied", "Occupied"),
        ("unavailable", "Unavailable"),
    ]

    FURNISHING_CHOICES = [
        ("furnished", "Furnished"),
        ("unfurnished", "Unfurnished"),
        ("semi", "Semi-Furnished"),
    ]

    # Owner
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="properties")

    # Basic Info
    title = models.CharField(max_length=200)
    type = models.CharField(max_length=20, choices=PROPERTY_TYPES)
    rent_type = models.CharField(max_length=10, choices=RENT_TYPES, default="whole")
    description = models.TextField(blank=True)

    # Location
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    landmark = models.CharField(
        max_length=200, blank=True, help_text="e.g. Near bus stop, Near school"
    )

    # Property Size (for whole property)
    total_floors = models.PositiveIntegerField(default=1)
    total_rooms = models.PositiveIntegerField(default=1)
    total_bedrooms = models.PositiveIntegerField(default=1)
    total_bathrooms = models.PositiveIntegerField(default=1)
    total_kitchens = models.PositiveIntegerField(default=1)
    bathrooms_per_floor = models.PositiveIntegerField(default=1)
    area_sqft = models.PositiveIntegerField(
        null=True, blank=True, help_text="Total area in sq ft"
    )

    # Amenities
    furnishing = models.CharField(
        max_length=20, choices=FURNISHING_CHOICES, default="unfurnished"
    )
    has_parking = models.BooleanField(default=False)
    has_water_supply = models.BooleanField(default=True)
    has_electricity_backup = models.BooleanField(default=False)
    has_internet = models.BooleanField(default=False)
    has_garden = models.BooleanField(default=False)
    has_balcony = models.BooleanField(default=False)

    # Pricing (only for whole property rent)
    rent_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    security_deposit = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    advance_months = models.PositiveIntegerField(
        default=1, help_text="Advance payment in months"
    )

    # Status
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="available"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Properties"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({self.get_type_display()}) — {self.city}"

    def is_available(self):
        return self.status == "available"

    def is_whole(self):
        return self.rent_type == "whole"

    def is_rooms(self):
        return self.rent_type == "rooms"

    def available_rooms(self):
        return self.rooms.filter(status="available")


class PropertyPhoto(models.Model):
    property = models.ForeignKey(
        Property, on_delete=models.CASCADE, related_name="photos"
    )
    image = models.ImageField(upload_to="properties/")
    caption = models.CharField(max_length=100, blank=True)
    is_cover = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Photo — {self.property.title}"


class Room(models.Model):
    ROOM_TYPES = [
        ("single", "Single Room"),
        ("double", "Double Room"),
        ("triple", "Triple Room"),
        ("studio", "Studio"),
        ("suite", "Suite"),
        ("other", "Other"),
    ]

    BATHROOM_TYPES = [
        ("attached", "Attached"),
        ("shared", "Shared"),
    ]

    KITCHEN_TYPES = [
        ("attached", "Attached"),
        ("shared", "Shared"),
        ("none", "No Kitchen"),
    ]

    FURNISHING_CHOICES = [
        ("furnished", "Furnished"),
        ("unfurnished", "Unfurnished"),
        ("semi", "Semi-Furnished"),
    ]

    STATUS_CHOICES = [
        ("available", "Available"),
        ("occupied", "Occupied"),
        ("unavailable", "Unavailable"),
    ]

    # Property it belongs to
    property = models.ForeignKey(
        Property, on_delete=models.CASCADE, related_name="rooms"
    )

    # Basic Info
    room_number = models.CharField(
        max_length=20, help_text="e.g. 101, A1, Ground Floor Room"
    )
    room_type = models.CharField(max_length=20, choices=ROOM_TYPES, default="single")
    description = models.TextField(blank=True)

    # Room Details
    bedrooms = models.PositiveIntegerField(default=1)
    bathroom_type = models.CharField(
        max_length=20, choices=BATHROOM_TYPES, default="shared"
    )
    kitchen_type = models.CharField(
        max_length=20, choices=KITCHEN_TYPES, default="shared"
    )
    floor_number = models.PositiveIntegerField(default=1)
    area_sqft = models.PositiveIntegerField(
        null=True, blank=True, help_text="Area in sq ft"
    )
    furnishing = models.CharField(
        max_length=20, choices=FURNISHING_CHOICES, default="unfurnished"
    )

    # Pricing
    rent_price = models.DecimalField(max_digits=10, decimal_places=2)
    security_deposit = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    advance_months = models.PositiveIntegerField(default=1)

    # Status
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="available"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["floor_number", "room_number"]
        unique_together = [
            "property",
            "room_number",
        ]  # no duplicate room numbers in same property

    def __str__(self):
        return f"Room {self.room_number} — {self.property.title}"

    def is_available(self):
        return self.status == "available"


class RoomFacility(models.Model):
    room = models.OneToOneField(Room, on_delete=models.CASCADE, related_name="facility")

    # Utilities
    wifi = models.BooleanField(default=False)
    water_included = models.BooleanField(default=False)
    electricity_included = models.BooleanField(default=False)
    gas_included = models.BooleanField(default=False)

    # Appliances
    ac = models.BooleanField(default=False)
    heater = models.BooleanField(default=False)
    refrigerator = models.BooleanField(default=False)
    washing_machine = models.BooleanField(default=False)
    tv = models.BooleanField(default=False)
    microwave = models.BooleanField(default=False)

    # Space
    kitchen = models.BooleanField(default=False)
    parking = models.BooleanField(default=False)
    balcony = models.BooleanField(default=False)
    garden = models.BooleanField(default=False)
    storage = models.BooleanField(default=False)

    # Services
    laundry = models.BooleanField(default=False)
    security_guard = models.BooleanField(default=False)
    cctv = models.BooleanField(default=False)
    lift = models.BooleanField(default=False)
    housekeeping = models.BooleanField(default=False)

    # Furnishing
    furnished = models.BooleanField(default=False)
    bed = models.BooleanField(default=False)
    wardrobe = models.BooleanField(default=False)
    study_table = models.BooleanField(default=False)
    sofa = models.BooleanField(default=False)

    def __str__(self):
        return f"Facilities — Room {self.room.room_number}"


class RoomPhoto(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="photos")
    image = models.ImageField(upload_to="rooms/")
    caption = models.CharField(max_length=100, blank=True)
    is_cover = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Photo — Room {self.room.room_number}"
