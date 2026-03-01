from .base import *
import os

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

import dj_database_url
from decouple import config
 
DEBUG = False
ALLOWED_HOSTS = [config('ALLOWED_HOSTS', default='https://Rent_Management_System.onrender.com').split(',')]
 
# PostgreSQL — switch simply by deploying with this settings file
# All credentials come from .env (never hardcoded)

DATABASES = {
    'default': dj_database_url.config(
        default=config('DATABASE_URL')
    )
}
 
 
# Static files served by whitenoise (no nginx needed for static)
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
 
# Security headers
SECURE_SSL_REDIRECT    = True
SESSION_COOKIE_SECURE  = True
CSRF_COOKIE_SECURE     = True
 
# Real email via SMTP (set in .env)
EMAIL_BACKEND  = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST     = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT     = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS  = True
EMAIL_HOST_USER     = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
