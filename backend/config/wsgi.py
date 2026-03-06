"""
WSGI config — entry point for production web servers (Gunicorn).
DJANGO_SETTINGS_MODULE points to our dev settings by default.
In production, override this env var to use config.settings.prod
"""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
application = get_wsgi_application()
