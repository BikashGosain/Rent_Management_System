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
 
INSTALLED_APPS += ['debug_toolbar']
MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
INTERNAL_IPS = ['127.0.0.1']
 
# Emails print to terminal — no SMTP needed during development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
