from rest_framework import serializers
from django.utils import timezone

from .models import Appointment
from apps.accounts.serializers import UserMinimalSerializer
from apps.doctors.serializers import DoctorListSerializer


class AppointmentSerializer(serializers.ModelSerializer):
    """Full appointment detail — used for retrieve and list."""
    patient = UserMinimalSerializer(read_only=True)
    doctor_detail = DoctorListSerializer(source="doctor", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    can_cancel = serializers.BooleanField(source="can_be_cancelled", read_only=True)

    class Meta:
        model = Appointment
        fields = [
            "id", "patient", "doctor", "doctor_detail",
            "appointment_date", "appointment_time",
            "status", "status_display", "reason", "notes",
            "cancellation_reason", "can_cancel",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "patient", "status", "notes", "created_at", "updated_at"]


class BookAppointmentSerializer(serializers.ModelSerializer):
    """
    Used when a patient books a new appointment.
    Patient is set from request.user — cannot be spoofed.
    """

    class Meta:
        model = Appointment
        fields = ["doctor", "appointment_date", "appointment_time", "reason"]

    def validate_appointment_date(self, value):
        if value < timezone.now().date():
            raise serializers.ValidationError("Cannot book an appointment in the past.")
        return value

    def validate(self, attrs):
        # Check slot availability
        doctor = attrs["doctor"]
        date = attrs["appointment_date"]
        time = attrs["appointment_time"]

        conflict = Appointment.objects.filter(
            doctor=doctor,
            appointment_date=date,
            appointment_time=time,
            status__in=["pending", "confirmed"],
        ).exists()

        if conflict:
            raise serializers.ValidationError(
                {"appointment_time": "This slot is already booked. Please choose another time."}
            )

        # Check doctor is available on this day
        day_of_week = date.weekday()
        if not doctor.availability.filter(day_of_week=day_of_week, is_active=True).exists():
            raise serializers.ValidationError(
                {"appointment_date": "The doctor is not available on this day."}
            )

        return attrs

    def create(self, validated_data):
        # Patient is always the current user
        validated_data["patient"] = self.context["request"].user
        return super().create(validated_data)


class UpdateAppointmentSerializer(serializers.ModelSerializer):
    """
    Used to update status (doctor/admin) or reschedule (patient).
    Different roles can update different fields.
    """

    class Meta:
        model = Appointment
        fields = [
            "appointment_date", "appointment_time",
            "status", "notes", "cancellation_reason",
        ]

    def validate_status(self, value):
        instance = self.instance
        user = self.context["request"].user

        # Patients can only cancel
        if user.is_patient and value not in [Appointment.Status.CANCELLED]:
            raise serializers.ValidationError(
                "Patients can only cancel appointments."
            )

        # Can't un-cancel or un-complete
        if instance.status in [Appointment.Status.COMPLETED, Appointment.Status.CANCELLED]:
            raise serializers.ValidationError(
                f"Cannot change status of a {instance.status} appointment."
            )

        return value


class AppointmentListSerializer(serializers.ModelSerializer):
    """Lightweight for list views."""
    doctor_name = serializers.CharField(source="doctor.user.get_full_name")
    patient_name = serializers.CharField(source="patient.get_full_name")
    status_display = serializers.CharField(source="get_status_display")
    specialization = serializers.CharField(source="doctor.specialization.name")

    class Meta:
        model = Appointment
        fields = [
            "id", "doctor_name", "patient_name", "specialization",
            "appointment_date", "appointment_time",
            "status", "status_display", "created_at",
        ]
