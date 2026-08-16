#!/bin/bash

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --noinput --settings=config.settings.production

# Run migrations
python manage.py migrate --settings=config.settings.production


python manage.py create_superuser_default --settings=config.settings.production