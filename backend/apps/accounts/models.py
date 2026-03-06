from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom User model — the single source of truth for all user types.

    WHY extend AbstractUser instead of AbstractBaseUser?
    AbstractUser gives us username, email, password, is_staff, is_active,
    date_joined, first_name, last_name for free. We just ADD our fields.
    AbstractBaseUser is for when you want to build everything from scratch.

    The 'role' field controls what each user can do:
      - admin:   full system access
      - doctor:  manage own schedule, view own appointments
      - patient: book/manage own appointments
    """

    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        DOCTOR = "doctor", "Doctor"
        PATIENT = "patient", "Patient"

    # Override email to make it unique — we use email for login
    email = models.EmailField(unique=True)

    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.PATIENT,
    )
    phone = models.CharField(max_length=15, blank=True)
    profile_picture = models.ImageField(
        upload_to="profiles/",
        blank=True,
        null=True,
    )
    date_of_birth = models.DateField(blank=True, null=True)
    address = models.TextField(blank=True)
    is_email_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Use email as the primary login field instead of username
    USERNAME_FIELD = "email"
    # username is still required when creating via createsuperuser
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    class Meta:
        db_table = "users"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_full_name()} <{self.email}> [{self.role}]"

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN

    @property
    def is_doctor(self):
        return self.role == self.Role.DOCTOR

    @property
    def is_patient(self):
        return self.role == self.Role.PATIENT
