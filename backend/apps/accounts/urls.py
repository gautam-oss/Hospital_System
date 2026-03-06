from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    LoginView,
    RegisterView,
    LogoutView,
    ProfileView,
    ChangePasswordView,
    AdminUserListView,
    AdminUserDetailView,
)

# All prefixed with /api/v1/auth/ from root urls.py
urlpatterns = [
    # ── Authentication ────────────────────────────────────────
    path("register/", RegisterView.as_view(), name="auth-register"),
    path("login/", LoginView.as_view(), name="auth-login"),
    path("logout/", LogoutView.as_view(), name="auth-logout"),

    # JWT token management
    # TokenRefreshView is provided by simplejwt — handles rotation automatically
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),

    # ── Profile ───────────────────────────────────────────────
    path("profile/", ProfileView.as_view(), name="auth-profile"),
    path("change-password/", ChangePasswordView.as_view(), name="auth-change-password"),

    # ── Admin ─────────────────────────────────────────────────
    path("admin/users/", AdminUserListView.as_view(), name="admin-user-list"),
    path("admin/users/<int:pk>/", AdminUserDetailView.as_view(), name="admin-user-detail"),
]
