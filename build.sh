#!/bin/bash

# Install dependencies
pip install -r requirements/production.txt

# Collect static files
python manage.py collectstatic --noinput

# Fix migration order for Render deploy
# Fake initial migrations to prevent "already applied" errors
python manage.py migrate accounts 0001_initial --fake
python manage.py migrate accounts 0002_user_phone_user_photo_user_role --fake
python manage.py migrate accounts 0003_user_address_user_bio_user_is_google_and_more --fake
python manage.py migrate accounts 0004_alter_user_role --fake

# Apply remaining migrations normally
python manage.py migrate