from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone


class Appointment(models.Model):
    """
    Core model of the entire system.

    Status flow:
      pending → confirmed → completed
         ↓           ↓
      cancelled   cancelled

    WHY store appointment_date and appointment_time separately?
    Makes querying easier: filter by date, group by time slot,
    check for conflicts on a specific date.
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"         # just booked, awaiting confirmation
        CONFIRMED = "confirmed", "Confirmed"   # doctor/admin confirmed
        COMPLETED = "completed", "Completed"   # appointment happened
        CANCELLED = "cancelled", "Cancelled"   # cancelled by patient or doctor
        NO_SHOW = "no_show", "No Show"         # patient didn't show up

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="appointments_as_patient",
    )
    doctor = models.ForeignKey(
        "doctors.DoctorProfile",
        on_delete=models.CASCADE,
        related_name="appointments",
    )
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,  # we query by status often
    )
    reason = models.TextField(
        help_text="Reason for the appointment / symptoms"
    )
    notes = models.TextField(
        blank=True,
        help_text="Doctor's notes after the appointment",
    )
    cancellation_reason = models.TextField(blank=True)
    cancelled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cancellations",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "appointments"
        ordering = ["-appointment_date", "-appointment_time"]
        indexes = [
            # Speeds up "get all appointments for doctor on date" queries
            models.Index(fields=["doctor", "appointment_date"]),
            # Speeds up "get all appointments for patient" queries
            models.Index(fields=["patient", "status"]),
        ]

    def __str__(self):
        return (
            f"{self.patient.get_full_name()} → "
            f"Dr. {self.doctor.user.get_full_name()} "
            f"on {self.appointment_date} at {self.appointment_time}"
        )

    def clean(self):
        """
        Model-level validation — runs before save().
        Prevents double-booking at the database level.
        """
        if self.appointment_date and self.appointment_date < timezone.now().date():
            raise ValidationError("Cannot book an appointment in the past.")

        # Check for conflicts (same doctor, same date, same time, not cancelled)
        conflicts = Appointment.objects.filter(
            doctor=self.doctor,
            appointment_date=self.appointment_date,
            appointment_time=self.appointment_time,
            status__in=[self.Status.PENDING, self.Status.CONFIRMED],
        ).exclude(pk=self.pk)  # exclude self when updating

        if conflicts.exists():
            raise ValidationError(
                "This time slot is already booked. Please choose another time."
            )

    def save(self, *args, **kwargs):
        self.full_clean()  # always run validation before save
        super().save(*args, **kwargs)

    @property
    def can_be_cancelled(self):
        return self.status in [self.Status.PENDING, self.Status.CONFIRMED]

    @property
    def is_upcoming(self):
        from datetime import datetime
        appointment_dt = datetime.combine(self.appointment_date, self.appointment_time)
        return appointment_dt > timezone.now().replace(tzinfo=None)
