from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom User model — extends Django's built-in user.
    We define roles and extra fields here.
    Full implementation in Phase 2.
    """
    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        DOCTOR = "doctor", "Doctor"
        PATIENT = "patient", "Patient"

    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.PATIENT,
    )
    phone = models.CharField(max_length=15, blank=True)

    def __str__(self):
        return f"{self.email} ({self.role})"
