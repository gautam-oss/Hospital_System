"""
SERIALIZERS — convert between Python objects ↔ JSON

Think of serializers as both:
  1. A form validator (validates incoming data)
  2. A JSON formatter (shapes outgoing data)

DRF serializers handle both directions automatically.
"""

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import get_user_model

User = get_user_model()


# ── JWT CUSTOMIZATION ─────────────────────────────────────────
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Adds extra claims to the JWT payload.

    By default JWT only contains user_id. We add role and email
    so the React frontend doesn't need an extra API call to know
    who the current user is and what they're allowed to do.

    Token payload becomes:
    {
        "user_id": 42,
        "email": "doctor@hospital.com",
        "role": "doctor",
        "name": "Dr. Smith",
        "exp": 1234567890
    }
    """

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Add custom claims
        token["email"] = user.email
        token["role"] = user.role
        token["name"] = user.get_full_name()
        return token


# ── REGISTRATION ──────────────────────────────────────────────
class RegisterSerializer(serializers.ModelSerializer):
    """
    Handles patient self-registration.
    Doctors are created by admins only (different endpoint).
    """

    password = serializers.CharField(
        write_only=True,       # never returned in response
        required=True,
        validators=[validate_password],  # Django's built-in password rules
    )
    password_confirm = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = [
            "email", "username", "first_name", "last_name",
            "password", "password_confirm", "phone", "date_of_birth",
        ]
        extra_kwargs = {
            "first_name": {"required": True},
            "last_name": {"required": True},
        }

    def validate(self, attrs):
        # Check passwords match
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {"password": "Passwords do not match."}
            )
        return attrs

    def create(self, validated_data):
        # Remove confirm field before creating user
        validated_data.pop("password_confirm")
        # Always register as patient — role cannot be self-assigned
        user = User.objects.create_user(
            **validated_data,
            role=User.Role.PATIENT,
        )
        return user


# ── USER PROFILE ──────────────────────────────────────────────
class UserProfileSerializer(serializers.ModelSerializer):
    """
    Read/update current user's profile.
    Role and sensitive fields are read-only.
    """

    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id", "email", "username", "first_name", "last_name",
            "full_name", "role", "phone", "profile_picture",
            "date_of_birth", "address", "is_email_verified",
            "date_joined", "created_at",
        ]
        read_only_fields = [
            "id", "email", "role", "is_email_verified",
            "date_joined", "created_at",
        ]

    def get_full_name(self, obj):
        return obj.get_full_name()


# ── PASSWORD CHANGE ───────────────────────────────────────────
class ChangePasswordSerializer(serializers.Serializer):
    """
    Separate serializer for password change — requires old password.
    Forces users to prove they know their current password before changing.
    """

    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(
        required=True,
        validators=[validate_password],
    )
    new_password_confirm = serializers.CharField(required=True)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError(
                {"new_password": "Passwords do not match."}
            )
        return attrs

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value


# ── ADMIN: CREATE USER ────────────────────────────────────────
class AdminCreateUserSerializer(serializers.ModelSerializer):
    """
    Used by admins to create doctor accounts.
    Allows setting role explicitly.
    """

    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = [
            "email", "username", "first_name", "last_name",
            "password", "role", "phone",
        ]

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


# ── MINIMAL USER (used by other apps) ─────────────────────────
class UserMinimalSerializer(serializers.ModelSerializer):
    """
    Lightweight user info — used when embedding user inside
    other serializers (e.g. inside AppointmentSerializer).
    Avoids exposing sensitive fields.
    """

    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "full_name", "email", "phone", "profile_picture"]

    def get_full_name(self, obj):
        return obj.get_full_name()
