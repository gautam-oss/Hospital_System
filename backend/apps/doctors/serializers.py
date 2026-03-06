from rest_framework import serializers
from django.utils import timezone
from datetime import datetime, timedelta

from .models import Specialization, DoctorProfile, DoctorAvailability
from apps.accounts.serializers import UserMinimalSerializer


class SpecializationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Specialization
        fields = ["id", "name", "description", "icon"]


class DoctorAvailabilitySerializer(serializers.ModelSerializer):
    day_name = serializers.CharField(
        source="get_day_of_week_display", read_only=True
    )

    class Meta:
        model = DoctorAvailability
        fields = [
            "id", "day_of_week", "day_name",
            "start_time", "end_time", "slot_duration_minutes", "is_active",
        ]


class DoctorProfileSerializer(serializers.ModelSerializer):
    """Full doctor profile — used for detail views."""
    user = UserMinimalSerializer(read_only=True)
    specialization = SpecializationSerializer(read_only=True)
    specialization_id = serializers.PrimaryKeyRelatedField(
        queryset=Specialization.objects.all(),
        source="specialization",
        write_only=True,
    )
    availability = DoctorAvailabilitySerializer(many=True, read_only=True)

    class Meta:
        model = DoctorProfile
        fields = [
            "id", "user", "specialization", "specialization_id",
            "license_number", "bio", "years_of_experience",
            "consultation_fee", "is_available", "rating",
            "total_reviews", "availability",
        ]
        read_only_fields = ["rating", "total_reviews"]


class DoctorListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views — no nested availability."""
    full_name = serializers.CharField(source="user.get_full_name")
    email = serializers.EmailField(source="user.email")
    profile_picture = serializers.ImageField(source="user.profile_picture")
    specialization_name = serializers.CharField(source="specialization.name")

    class Meta:
        model = DoctorProfile
        fields = [
            "id", "full_name", "email", "profile_picture",
            "specialization_name", "years_of_experience",
            "consultation_fee", "is_available", "rating",
        ]


class AvailableSlotsSerializer(serializers.Serializer):
    """
    Not a model serializer — generates available time slots for a given date.

    Input:  doctor_id + date
    Output: list of available datetime slots
    """
    date = serializers.DateField()

    def get_slots(self, doctor_profile):
        date = self.validated_data["date"]

        # Check if date is in the past
        if date < timezone.now().date():
            return []

        # Get the doctor's availability for this day of the week
        day_of_week = date.weekday()  # 0=Monday, 6=Sunday
        try:
            availability = doctor_profile.availability.get(
                day_of_week=day_of_week, is_active=True
            )
        except DoctorAvailability.DoesNotExist:
            return []  # Doctor doesn't work on this day

        # Generate all slots
        slots = []
        current = datetime.combine(date, availability.start_time)
        end = datetime.combine(date, availability.end_time)
        delta = timedelta(minutes=availability.slot_duration_minutes)

        # Import here to avoid circular import
        from apps.appointments.models import Appointment

        # Get already-booked slots for this doctor on this date
        booked_times = set(
            Appointment.objects.filter(
                doctor=doctor_profile,
                appointment_date=date,
                status__in=["pending", "confirmed"],
            ).values_list("appointment_time", flat=True)
        )

        while current + delta <= end:
            slot_time = current.time()
            slots.append({
                "time": slot_time.strftime("%H:%M"),
                "available": slot_time not in booked_times,
            })
            current += delta

        return slots
