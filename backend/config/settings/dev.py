"""
DEV SETTINGS
Overrides base.py for local development.
Never use these settings in production.
"""

from .base import *  # noqa: F401, F403
from decouple import config

# ─── DEBUG ────────────────────────────────────────────────────
# Shows detailed error pages when something goes wrong.
# NEVER True in production — it leaks source code and settings.
DEBUG = config("DJANGO_DEBUG", cast=bool, default=True)


# ─── DEV-ONLY APPS ───────────────────────────────────────────
INSTALLED_APPS += [  # noqa: F405
    "django_extensions",   # adds shell_plus, show_urls, etc.
]


# ─── DJANGO EXTENSIONS ───────────────────────────────────────
# shell_plus auto-imports all your models when you run:
# python manage.py shell_plus
SHELL_PLUS = "ipython"
SHELL_PLUS_PRINT_SQL = True   # shows the SQL query for every ORM call


# ─── EMAIL ───────────────────────────────────────────────────
# In dev, print emails to console instead of sending real emails.
# You'll see the email content in Docker logs.
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"


# ─── CORS ─────────────────────────────────────────────────────
# In dev, allow ALL origins so you can test from anywhere.
CORS_ALLOW_ALL_ORIGINS = True
