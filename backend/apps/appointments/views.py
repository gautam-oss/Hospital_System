import logging
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter

from .models import Appointment
from .serializers import (
    AppointmentSerializer,
    AppointmentListSerializer,
    BookAppointmentSerializer,
    UpdateAppointmentSerializer,
)
from apps.accounts.permissions import IsAdmin, IsPatient, IsAdminOrDoctor, IsOwnerOrAdmin

logger = logging.getLogger(__name__)


class AppointmentListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/v1/appointments/  → list appointments (filtered by role)
    POST /api/v1/appointments/  → book a new appointment (patients only)

    KEY DESIGN: Role-based queryset.
    - Patient sees ONLY their own appointments
    - Doctor sees ONLY appointments with them
    - Admin sees ALL appointments

    This is enforced in get_queryset(), not just in permissions.
    Even if a patient guesses an appointment ID, they can't see it.
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["status", "appointment_date"]
    ordering_fields = ["appointment_date", "created_at"]
    ordering = ["-appointment_date"]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return BookAppointmentSerializer
        return AppointmentListSerializer

    def get_queryset(self):
        user = self.request.user

        # Base queryset with related data pre-fetched (avoids N+1)
        qs = Appointment.objects.select_related(
            "patient", "doctor__user", "doctor__specialization"
        )

        if user.is_patient:
            return qs.filter(patient=user)
        elif user.is_doctor:
            return qs.filter(doctor__user=user)
        elif user.is_admin:
            return qs.all()

        return qs.none()

    def create(self, request, *args, **kwargs):
        # Only patients can book
        if not request.user.is_patient:
            return Response(
                {"error": "Only patients can book appointments."},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = BookAppointmentSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        appointment = serializer.save()

        logger.info(
            f"Appointment booked: {appointment.patient.email} → "
            f"Dr. {appointment.doctor.user.get_full_name()} on {appointment.appointment_date}"
        )

        return Response(
            AppointmentSerializer(appointment).data,
            status=status.HTTP_201_CREATED,
        )


class AppointmentDetailView(generics.RetrieveUpdateAPIView):
    """
    GET   /api/v1/appointments/<id>/  → view appointment
    PATCH /api/v1/appointments/<id>/  → update status or reschedule
    """
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def get_serializer_class(self):
        if self.request.method in ["PATCH", "PUT"]:
            return UpdateAppointmentSerializer
        return AppointmentSerializer

    def get_queryset(self):
        user = self.request.user
        qs = Appointment.objects.select_related(
            "patient", "doctor__user", "doctor__specialization", "cancelled_by"
        )
        if user.is_patient:
            return qs.filter(patient=user)
        elif user.is_doctor:
            return qs.filter(doctor__user=user)
        return qs.all()

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", True)  # always allow partial updates
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        # Track who cancelled
        if serializer.validated_data.get("status") == Appointment.Status.CANCELLED:
            serializer.save(cancelled_by=request.user)
        else:
            serializer.save()

        logger.info(
            f"Appointment {instance.id} updated by {request.user.email}: "
            f"status={instance.status}"
        )

        return Response(AppointmentSerializer(instance).data)


class AdminAppointmentStatsView(APIView):
    """
    GET /api/v1/appointments/admin/stats/
    Dashboard stats for admin.
    """
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        from django.db.models import Count
        from django.utils import timezone

        today = timezone.now().date()

        stats = {
            "total": Appointment.objects.count(),
            "today": Appointment.objects.filter(appointment_date=today).count(),
            "pending": Appointment.objects.filter(status="pending").count(),
            "confirmed": Appointment.objects.filter(status="confirmed").count(),
            "completed": Appointment.objects.filter(status="completed").count(),
            "cancelled": Appointment.objects.filter(status="cancelled").count(),
            "by_status": list(
                Appointment.objects.values("status")
                .annotate(count=Count("id"))
                .order_by("status")
            ),
        }

        return Response({"success": True, "data": stats})
