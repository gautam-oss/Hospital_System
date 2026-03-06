"""
ACCOUNTS VIEWS

Each view is a class-based APIView or ViewSet.

WHY class-based views?
  - Cleaner separation of GET/POST/PATCH/DELETE logic
  - Easy to mix in permission classes
  - DRF's ViewSets reduce boilerplate for CRUD operations
"""

import logging
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model

from .serializers import (
    CustomTokenObtainPairSerializer,
    RegisterSerializer,
    UserProfileSerializer,
    ChangePasswordSerializer,
    AdminCreateUserSerializer,
)
from .permissions import IsAdmin

logger = logging.getLogger(__name__)
User = get_user_model()


# ── LOGIN ─────────────────────────────────────────────────────
class LoginView(TokenObtainPairView):
    """
    POST /api/v1/auth/login/
    Body: { "email": "...", "password": "..." }
    Returns: { "access": "...", "refresh": "..." }

    We just override the serializer to use our custom one
    that adds role/email/name to the JWT payload.
    """
    permission_classes = [AllowAny]
    serializer_class = CustomTokenObtainPairSerializer


# ── REGISTER ──────────────────────────────────────────────────
class RegisterView(generics.CreateAPIView):
    """
    POST /api/v1/auth/register/
    Body: { email, username, first_name, last_name, password, password_confirm }
    Returns: user data (no tokens — user must login separately)

    WHY not return tokens on register?
    Best practice: separate concerns. Register = create account.
    Login = authenticate. Forces explicit login step.
    """
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        logger.info(f"New patient registered: {user.email}")

        return Response(
            {
                "success": True,
                "message": "Account created successfully. Please log in.",
                "data": {"email": user.email, "id": user.id},
            },
            status=status.HTTP_201_CREATED,
        )


# ── LOGOUT ────────────────────────────────────────────────────
class LogoutView(APIView):
    """
    POST /api/v1/auth/logout/
    Body: { "refresh": "<refresh_token>" }

    Blacklists the refresh token so it can't be used again.
    The access token will naturally expire after 15 minutes.

    WHY blacklist on logout?
    JWTs are stateless — you can't "delete" them on the server.
    Blacklisting the refresh token prevents new access tokens
    from being issued after logout.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                return Response(
                    {"error": "Refresh token is required."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            token = RefreshToken(refresh_token)
            token.blacklist()
            logger.info(f"User logged out: {request.user.email}")
            return Response(
                {"success": True, "message": "Logged out successfully."},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"error": "Invalid token."},
                status=status.HTTP_400_BAD_REQUEST,
            )


# ── PROFILE ───────────────────────────────────────────────────
class ProfileView(generics.RetrieveUpdateAPIView):
    """
    GET  /api/v1/auth/profile/  → view your profile
    PATCH /api/v1/auth/profile/ → update your profile

    RetrieveUpdateAPIView handles both GET and PATCH/PUT.
    get_object() returns the currently authenticated user.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = UserProfileSerializer

    def get_object(self):
        # Always return the current user — no ID needed in URL
        return self.request.user


# ── CHANGE PASSWORD ───────────────────────────────────────────
class ChangePasswordView(APIView):
    """
    POST /api/v1/auth/change-password/
    Body: { old_password, new_password, new_password_confirm }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save()
        logger.info(f"Password changed for user: {request.user.email}")
        return Response(
            {"success": True, "message": "Password changed successfully."},
            status=status.HTTP_200_OK,
        )


# ── ADMIN: USER MANAGEMENT ────────────────────────────────────
class AdminUserListView(generics.ListCreateAPIView):
    """
    GET  /api/v1/auth/admin/users/         → list all users
    POST /api/v1/auth/admin/users/         → create a new user (any role)

    Admin only. Used to create doctor accounts.
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    serializer_class = AdminCreateUserSerializer
    queryset = User.objects.all().order_by("-created_at")

    # Allow filtering by role: /api/v1/auth/admin/users/?role=doctor
    def get_queryset(self):
        qs = super().get_queryset()
        role = self.request.query_params.get("role")
        if role:
            qs = qs.filter(role=role)
        return qs


class AdminUserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/v1/auth/admin/users/<id>/  → view user
    PATCH  /api/v1/auth/admin/users/<id>/  → update user
    DELETE /api/v1/auth/admin/users/<id>/  → deactivate user
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    serializer_class = UserProfileSerializer
    queryset = User.objects.all()

    def destroy(self, request, *args, **kwargs):
        # Soft delete — deactivate instead of actual delete
        # Preserves data integrity (appointments still have user records)
        user = self.get_object()
        user.is_active = False
        user.save()
        return Response(
            {"success": True, "message": "User deactivated."},
            status=status.HTTP_200_OK,
        )
