"""
ROOT URL CONFIGURATION

All API routes live under /api/v1/ — versioning from day one.
Why version? If you ever break the API (Phase 2 → Phase 3),
clients on v1 keep working while new clients use v2.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

urlpatterns = [
    # Django admin panel — available at /admin/
    path("admin/", admin.site.urls),

    # ── API v1 ──────────────────────────────────────────────
    path("api/v1/auth/", include("apps.accounts.urls")),  # Phase 2
    path("api/v1/doctors/", include("apps.doctors.urls")),  # Phase 2
    path("api/v1/appointments/", include("apps.appointments.urls")),  # Phase 

    # ── API Documentation ────────────────────────────────────
    # /api/schema/          → raw OpenAPI JSON
    # /api/docs/            → Swagger UI (interactive)
    # /api/redoc/           → ReDoc (readable)
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]

# In development, serve uploaded media files directly
# In production, Nginx handles this more efficiently
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
