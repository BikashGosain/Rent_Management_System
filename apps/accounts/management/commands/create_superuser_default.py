import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Create default superuser if none exists'

    def handle(self, *args, **kwargs):
        if User.objects.filter(is_superuser=True).exists():
            self.stdout.write(self.style.WARNING('Superuser already exists. Skipping.'))
            return

        username = os.environ.get('SUPERUSER_USERNAME', 'admin')
        email    = os.environ.get('SUPERUSER_EMAIL',    'admin@rentms.com')
        password = os.environ.get('SUPERUSER_PASSWORD')

        if not password:
            self.stdout.write(self.style.ERROR(
                'SUPERUSER_PASSWORD environment variable not set. Skipping.'
            ))
            return

        User.objects.create_superuser(
            username   = username,
            email      = email,
            password   = password,
            first_name = 'Super',
            last_name  = 'Admin',
            role       = 'admin',
        )
        self.stdout.write(self.style.SUCCESS(
            f'Superuser created → username: {username}'
        ))
