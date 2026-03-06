from django.db import models
from django.conf import settings


class Specialization(models.Model):
    """
    Medical specializations — e.g. Cardiology, Neurology.
    Separate model so admins can manage them without code changes.
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)  # emoji or icon class

    class Meta:
        db_table = "specializations"
        ordering = ["name"]

    def __str__(self):
        return self.name


class DoctorProfile(models.Model):
    """
    Extended profile for doctors. OneToOne with User.

    WHY a separate model instead of fields on User?
    Separation of concerns — not every user is a doctor.
    Keeps the User model lean and focused.
    DoctorProfile only exists when user.role == 'doctor'.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="doctor_profile",  # access via: user.doctor_profile
    )
    specialization = models.ForeignKey(
        Specialization,
        on_delete=models.SET_NULL,
        null=True,
        related_name="doctors",
    )
    license_number = models.CharField(max_length=50, unique=True)
    bio = models.TextField(blank=True)
    years_of_experience = models.PositiveIntegerField(default=0)
    consultation_fee = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0.00,
    )
    is_available = models.BooleanField(
        default=True,
        help_text="Toggle to temporarily disable new appointments",
    )
    rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.00,
    )
    total_reviews = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "doctor_profiles"

    def __str__(self):
        return f"Dr. {self.user.get_full_name()} — {self.specialization}"


class DoctorAvailability(models.Model):
    """
    Recurring weekly schedule for a doctor.
    Example: "Monday 9am–5pm, 30-minute slots"

    This defines WHEN a doctor works, not individual appointments.
    The appointment booking logic uses this to generate available slots.
    """

    class DayOfWeek(models.IntegerChoices):
        MONDAY = 0, "Monday"
        TUESDAY = 1, "Tuesday"
        WEDNESDAY = 2, "Wednesday"
        THURSDAY = 3, "Thursday"
        FRIDAY = 4, "Friday"
        SATURDAY = 5, "Saturday"
        SUNDAY = 6, "Sunday"

    doctor = models.ForeignKey(
        DoctorProfile,
        on_delete=models.CASCADE,
        related_name="availability",
    )
    day_of_week = models.IntegerField(choices=DayOfWeek.choices)
    start_time = models.TimeField()
    end_time = models.TimeField()
    slot_duration_minutes = models.PositiveIntegerField(
        default=30,
        help_text="Length of each appointment slot in minutes",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "doctor_availability"
        # A doctor can only have one schedule entry per day
        unique_together = ["doctor", "day_of_week"]
        ordering = ["day_of_week", "start_time"]

    def __str__(self):
        return (
            f"Dr. {self.doctor.user.get_full_name()} — "
            f"{self.get_day_of_week_display()} "
            f"{self.start_time}–{self.end_time}"
        )
