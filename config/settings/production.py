from .base import *  # noqa: F403, F405
import os

from decouple import config
import dj_database_url


# ============================================================
# BASIC SETTINGS
# ============================================================

DEBUG = False


# ============================================================
# ALLOWED HOSTS
# ============================================================

ALLOWED_HOSTS = [
    host.strip()
    for host in config(
        "ALLOWED_HOSTS",
        default=(
            "rent-management-system-1wyn.onrender.com,"
            "www.bikashgosain.com.np,"
            "bikashgosain.com.np,"
            "127.0.0.1,"
            "localhost"
        ),
    ).split(",")
    if host.strip()
]


# ============================================================
# DATABASE
# ============================================================

DATABASE_URL = config("DATABASE_URL")

DATABASES = {
    "default": dj_database_url.parse(
        DATABASE_URL,
        conn_max_age=600,
    )
}


# ============================================================
# STATIC FILES
# ============================================================

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")  # noqa: F405
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MIDDLEWARE.insert(  # noqa: F405
    1,
    "whitenoise.middleware.WhiteNoiseMiddleware",
)


# ============================================================
# SECURITY
# ============================================================

SECURE_SSL_REDIRECT = False

SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False


# ============================================================
# EMAIL
# ============================================================

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

EMAIL_HOST = config(
    "EMAIL_HOST",
    default="smtp.gmail.com",
)

EMAIL_PORT = config(
    "EMAIL_PORT",
    default=587,
    cast=int,
)

EMAIL_USE_TLS = True

EMAIL_HOST_USER = config("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD")

DEFAULT_FROM_EMAIL = f"RentMS <{EMAIL_HOST_USER}>"
