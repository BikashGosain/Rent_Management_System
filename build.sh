#!/bin/bash

# Install dependencies
pip install -r requirements/production.txt

# Collect static files
python manage.py collectstatic --noinput

# Run migrations
python manage.py migrate


python manage.py create_superuser_default