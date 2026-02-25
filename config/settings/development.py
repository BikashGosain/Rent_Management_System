from .base import *
 
DEBUG = True
ALLOWED_HOSTS = ['*']
 
# SQLite — zero setup, file lives at project root as db.sqlite3
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
 
INSTALLED_APPS += [
    'debug_toolbar',
]

MIDDLEWARE += [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
]
 
# Emails print to terminal — no SMTP needed during development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
