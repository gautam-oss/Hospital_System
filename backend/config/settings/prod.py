"""
PRODUCTION SETTINGS
These overrides make Django secure and performant for real traffic.
"""

from .base import *  # noqa: F401, F403
from decouple import config

DEBUG = False  # NEVER True in production

# ─── SECURITY HEADERS ────────────────────────────────────────
# These HTTP headers tell browsers to be extra cautious.

# Forces browsers to use HTTPS for 1 year (31536000 seconds)
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

SECURE_SSL_REDIRECT = True             # redirect HTTP → HTTPS
SESSION_COOKIE_SECURE = True           # cookie only sent over HTTPS
CSRF_COOKIE_SECURE = True              # CSRF cookie only over HTTPS
SECURE_BROWSER_XSS_FILTER = True       # XSS protection header
SECURE_CONTENT_TYPE_NOSNIFF = True     # prevent MIME-type sniffing
X_FRAME_OPTIONS = "DENY"              # prevent clickjacking


# ─── STATIC FILES ────────────────────────────────────────────
# In production, WhiteNoise serves static files efficiently
# without needing a separate file server.
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"


# ─── LOGGING ─────────────────────────────────────────────────
# In production, write errors to a file AND console.
LOGGING["handlers"]["file"] = {  # noqa: F405
    "class": "logging.FileHandler",
    "filename": "/app/logs/django.log",
    "formatter": "verbose",
}
LOGGING["root"]["handlers"] = ["console", "file"]  # noqa: F405
