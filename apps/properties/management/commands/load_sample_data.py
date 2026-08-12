import csv
import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.properties.models import Property, PropertyPhoto, Room, RoomFacility, RoomPhoto

User = get_user_model()
CSV_DIR = os.path.join(os.path.dirname(__file__), '../../../../csv_data')

def bool_val(v):
    return v.strip().lower() == 'true'

class Command(BaseCommand):
    help = 'Load sample CSV data into the database'

    def handle(self, *args, **kwargs):
        self.load_users()
        self.load_properties()
        self.load_property_photos()
        self.load_rooms()
        self.load_room_facilities()
        self.load_room_photos()
        self.stdout.write(self.style.SUCCESS('✅ All sample data loaded!'))

    def load_users(self):
        with open(f'{CSV_DIR}/users.csv') as f:
            for row in csv.DictReader(f):
                if not User.objects.filter(username=row['username']).exists():
                    User.objects.create_user(
                        id=row['id'],
                        username=row['username'],
                        email=row['email'],
                        first_name=row['first_name'],
                        last_name=row['last_name'],
                        password='password123',
                        role=row['role'],
                        phone=row['phone'],
                    )
        self.stdout.write('  → Users loaded')

    def load_properties(self):
        with open(f'{CSV_DIR}/properties.csv') as f:
            for row in csv.DictReader(f):
                owner = User.objects.get(id=row['owner_id'])
                Property.objects.get_or_create(id=row['id'], defaults={
                    'owner': owner,
                    'title': row['title'],
                    'type': row['type'],
                    'rent_type': row['rent_type'],
                    'description': row['description'],
                    'address': row['address'],
                    'city': row['city'],
                    'state': row['state'],
                    'landmark': row['landmark'],
                    'total_floors': int(row['total_floors']),
                    'total_rooms': int(row['total_rooms']),
                    'total_bedrooms': int(row['total_bedrooms']),
                    'total_bathrooms': int(row['total_bathrooms']),
                    'total_kitchens': int(row['total_kitchens']),
                    'area_sqft': int(row['area_sqft']) if row['area_sqft'] else None,
                    'furnishing': row['furnishing'],
                    'has_parking': bool_val(row['has_parking']),
                    'has_water_supply': bool_val(row['has_water_supply']),
                    'has_electricity_backup': bool_val(row['has_electricity_backup']),
                    'has_internet': bool_val(row['has_internet']),
                    'rent_price': row['rent_price'] or None,
                    'security_deposit': row['security_deposit'] or None,
                    'advance_months': int(row['advance_months']),
                    'status': row['status'],
                })
        self.stdout.write('  → Properties loaded')

    def load_property_photos(self):
        with open(f'{CSV_DIR}/property_photos.csv') as f:
            for row in csv.DictReader(f):
                prop = Property.objects.get(id=row['property_id'])
                PropertyPhoto.objects.get_or_create(id=row['id'], defaults={
                    'property': prop,
                    'image': row['image'],
                    'caption': row['caption'],
                    'is_cover': bool_val(row['is_cover']),
                })
        self.stdout.write('  → Property photos loaded')

    def load_rooms(self):
        with open(f'{CSV_DIR}/rooms.csv') as f:
            for row in csv.DictReader(f):
                prop = Property.objects.get(id=row['property_id'])
                Room.objects.get_or_create(id=row['id'], defaults={
                    'property': prop,
                    'room_number': row['room_number'],
                    'room_type': row['room_type'],
                    'description': row['description'],
                    'bedrooms': int(row['bedrooms']),
                    'bathroom_type': row['bathroom_type'],
                    'kitchen_type': row['kitchen_type'],
                    'floor_number': int(row['floor_number']),
                    'area_sqft': int(row['area_sqft']) if row['area_sqft'] else None,
                    'furnishing': row['furnishing'],
                    'rent_price': row['rent_price'],
                    'security_deposit': row['security_deposit'] or None,
                    'advance_months': int(row['advance_months']),
                    'status': row['status'],
                })
        self.stdout.write('  → Rooms loaded')

    def load_room_facilities(self):
        bool_fields = ['wifi','water_included','electricity_included','gas_included',
                       'ac','heater','refrigerator','washing_machine','tv','microwave',
                       'kitchen','parking','balcony','garden','storage',
                       'laundry','security_guard','cctv','lift','housekeeping',
                       'furnished','bed','wardrobe','study_table','sofa']
        with open(f'{CSV_DIR}/room_facilities.csv') as f:
            for row in csv.DictReader(f):
                room = Room.objects.get(id=row['room_id'])
                RoomFacility.objects.get_or_create(room=room, defaults={
                    field: bool_val(row[field]) for field in bool_fields
                })
        self.stdout.write('  → Room facilities loaded')

    def load_room_photos(self):
        with open(f'{CSV_DIR}/room_photos.csv') as f:
            for row in csv.DictReader(f):
                room = Room.objects.get(id=row['room_id'])
                RoomPhoto.objects.get_or_create(id=row['id'], defaults={
                    'room': room,
                    'image': row['image'],
                    'caption': row['caption'],
                    'is_cover': bool_val(row['is_cover']),
                })
        self.stdout.write('  → Room photos loaded')