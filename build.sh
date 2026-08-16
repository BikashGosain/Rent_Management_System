#!/bin/bash

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --noinput --settings=config.settings.production

# Run migrations
python manage.py migrate --settings=config.settings.production

# Create superuser
export SUPERUSER_USERNAME=$SUPERUSER_USERNAME
export SUPERUSER_EMAIL=$SUPERUSER_EMAIL
export SUPERUSER_PASSWORD=$SUPERUSER_PASSWORD
python manage.py create_superuser_default --settings=config.settings.production