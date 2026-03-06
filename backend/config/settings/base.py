"""
BASE SETTINGS — shared between development and production.

WHY SPLIT SETTINGS?
  config/settings/
    ├── base.py    ← shared config (this file)
    ├── dev.py     ← overrides for local development
    └── prod.py    ← overrides for production server

This pattern prevents accidentally deploying DEBUG=True to production,
and keeps secrets out of version control.

We use python-decouple to read values from the .env file.
"""

from pathlib import Path
from datetime import timedelta
from decouple import config, Csv

# Build paths inside the project: BASE_DIR / 'subdir'
# Path(__file__) = this file
# .resolve() = absolute path
# .parent.parent.parent = go up 3 levels to reach /app/
BASE_DIR = Path(__file__).resolve().parent.parent.parent


# ─────────────────────────────────────────────────────────────
# SECURITY
# ─────────────────────────────────────────────────────────────
SECRET_KEY = config("DJANGO_SECRET_KEY")

# Hosts that are allowed to serve this Django app.
# Using Csv() lets us set multiple hosts comma-separated in .env
ALLOWED_HOSTS = config("DJANGO_ALLOWED_HOSTS", cast=Csv())


# ─────────────────────────────────────────────────────────────
# INSTALLED APPS
# Order matters: apps earlier in the list can override templates
# from apps later in the list.
# ─────────────────────────────────────────────────────────────
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",               # Django REST Framework
    "rest_framework_simplejwt",     # JWT authentication
    "corsheaders",                  # CORS headers for React frontend
    "django_filters",               # filtering queryset in API
    "drf_spectacular",              # auto API docs
    "rest_framework_simplejwt.token_blacklist",
]

LOCAL_APPS = [
    "apps.core",
    "apps.accounts",
    "apps.doctors",
    "apps.appointments",
    "apps.notifications",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS


# ─────────────────────────────────────────────────────────────
# MIDDLEWARE
# Middleware is a pipeline. Every request passes through each
# middleware in order (top to bottom), and every response passes
# through in reverse (bottom to top).
# ─────────────────────────────────────────────────────────────
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",  # MUST be before CommonMiddleware
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# ─────────────────────────────────────────────────────────────
# DATABASE
# We use dj-database-url style via python-decouple.
# The host "db" matches the Docker Compose service name.
# ─────────────────────────────────────────────────────────────
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("POSTGRES_DB"),
        "USER": config("POSTGRES_USER"),
        "PASSWORD": config("POSTGRES_PASSWORD"),
        "HOST": "db",   # Docker service name, not "localhost"
        "PORT": "5432",
        "OPTIONS": {
            "connect_timeout": 10,
        },
        # Connection pooling — reuse DB connections instead of
        # opening a new one for every request
        "CONN_MAX_AGE": 60,
    }
}


# ─────────────────────────────────────────────────────────────
# CACHE (Redis)
# django-redis makes Redis work as Django's cache backend.
# We use cache for: API response caching, rate limiting counters,
# and storing JWT blacklist (invalidated tokens).
# ─────────────────────────────────────────────────────────────
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": config("REDIS_URL", default="redis://redis:6379/0"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "CONNECTION_POOL_KWARGS": {"max_connections": 50},
        },
        "KEY_PREFIX": "hospital",  # prefix all cache keys to avoid collisions
    }
}

# Use Redis for session storage too (instead of database)
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"


# ─────────────────────────────────────────────────────────────
# CUSTOM USER MODEL
# We extend AbstractUser to add role, phone, profile_pic.
# IMPORTANT: Set this BEFORE any migrations are created.
# Changing AUTH_USER_MODEL after migrations is very painful.
# ─────────────────────────────────────────────────────────────
AUTH_USER_MODEL = "accounts.User"


# ─────────────────────────────────────────────────────────────
# DJANGO REST FRAMEWORK
# Global DRF configuration — applies to all API views
# unless overridden per-view.
# ─────────────────────────────────────────────────────────────
REST_FRAMEWORK = {
    # All endpoints require a valid JWT by default.
    # Use AllowAny on specific views (e.g. login, register).
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    # Auto-paginate all list endpoints — prevents returning 10,000 records
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    # Enable filtering, searching, ordering on list views
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    # Use drf-spectacular for OpenAPI schema generation
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    # Consistent error format across all endpoints
    "EXCEPTION_HANDLER": "config.exceptions.custom_exception_handler",  # Phase 2
}


# ─────────────────────────────────────────────────────────────
# JWT SETTINGS
# Access token: short-lived (15 min) — if stolen, expires quickly
# Refresh token: longer-lived (7 days) — used to get new access tokens
# Rotation: every refresh call issues a NEW refresh token and
#           blacklists the old one (prevents token reuse attacks)
# ─────────────────────────────────────────────────────────────
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(
        minutes=config("JWT_ACCESS_TOKEN_LIFETIME_MINUTES", cast=int, default=15)
    ),
    "REFRESH_TOKEN_LIFETIME": timedelta(
        days=config("JWT_REFRESH_TOKEN_LIFETIME_DAYS", cast=int, default=7)
    ),
    "ROTATE_REFRESH_TOKENS": True,      # new refresh token on each refresh
    "BLACKLIST_AFTER_ROTATION": True,   # old refresh token becomes invalid
    "UPDATE_LAST_LOGIN": True,          # update User.last_login on token issue
    "ALGORITHM": "HS256",
    "AUTH_HEADER_TYPES": ("Bearer",),   # Authorization: Bearer <token>
    "TOKEN_OBTAIN_PAIR_SERIALIZER": "apps.accounts.serializers.CustomTokenObtainPairSerializer",
}


# ─────────────────────────────────────────────────────────────
# CORS (Cross-Origin Resource Sharing)
# Without this, browsers block React (port 5173) from calling
# Django (port 8000) due to the "same-origin policy".
# ─────────────────────────────────────────────────────────────
CORS_ALLOWED_ORIGINS = config("CORS_ALLOWED_ORIGINS", cast=Csv())
CORS_ALLOW_CREDENTIALS = True  # needed if using cookies/session auth


# ─────────────────────────────────────────────────────────────
# API DOCUMENTATION (drf-spectacular)
# ─────────────────────────────────────────────────────────────
SPECTACULAR_SETTINGS = {
    "TITLE": "Hospital Appointment System API",
    "DESCRIPTION": "REST API for managing hospital appointments, doctors, and patients.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}


# ─────────────────────────────────────────────────────────────
# STATIC & MEDIA FILES
# Static: CSS/JS/images bundled with the app code
# Media: user-uploaded files (profile pictures, etc.)
# ─────────────────────────────────────────────────────────────
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"  # where collectstatic puts files

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"         # where uploaded files are stored


# ─────────────────────────────────────────────────────────────
# EMAIL
# ─────────────────────────────────────────────────────────────
EMAIL_BACKEND = config(
    "EMAIL_BACKEND",
    default="django.core.mail.backends.console.EmailBackend"
)
EMAIL_HOST = config("EMAIL_HOST", default="smtp.gmail.com")
EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
EMAIL_USE_TLS = config("EMAIL_USE_TLS", default=True, cast=bool)
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = "Hospital System <noreply@hospital.com>"


# ─────────────────────────────────────────────────────────────
# LOGGING
# Structured logging sends errors to console + file.
# In production you'd ship logs to a service like Sentry.
# ─────────────────────────────────────────────────────────────
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{levelname}] {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "apps": {  # our custom apps
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
