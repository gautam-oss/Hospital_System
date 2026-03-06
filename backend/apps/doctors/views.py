import logging
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import Specialization, DoctorProfile, DoctorAvailability
from .serializers import (
    SpecializationSerializer,
    DoctorProfileSerializer,
    DoctorListSerializer,
    DoctorAvailabilitySerializer,
    AvailableSlotsSerializer,
)
from apps.accounts.permissions import IsAdmin, IsDoctor, IsOwnerOrAdminOrReadOnly

logger = logging.getLogger(__name__)


# ── SPECIALIZATIONS ───────────────────────────────────────────
class SpecializationListView(generics.ListCreateAPIView):
    """
    GET  /api/v1/doctors/specializations/  → list all (public)
    POST /api/v1/doctors/specializations/  → create (admin only)
    """
    queryset = Specialization.objects.all()
    serializer_class = SpecializationSerializer

    def get_permissions(self):
        # GET is public, POST requires admin
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated(), IsAdmin()]


# ── DOCTOR LIST ───────────────────────────────────────────────
class DoctorListView(generics.ListAPIView):
    """
    GET /api/v1/doctors/
    Public endpoint — patients browse doctors before registering.

    Supports:
      ?specialization=1          → filter by specialization ID
      ?search=cardiology         → search name/specialization
      ?ordering=rating           → sort by rating
      ?is_available=true         → only available doctors
    """
    serializer_class = DoctorListSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["specialization", "is_available"]
    search_fields = ["user__first_name", "user__last_name", "specialization__name"]
    ordering_fields = ["rating", "years_of_experience", "consultation_fee"]
    ordering = ["-rating"]

    def get_queryset(self):
        return DoctorProfile.objects.filter(
            user__is_active=True
        ).select_related("user", "specialization")  # avoids N+1 query


# ── DOCTOR DETAIL ─────────────────────────────────────────────
class DoctorDetailView(generics.RetrieveUpdateAPIView):
    """
    GET   /api/v1/doctors/<id>/  → view full profile (public)
    PATCH /api/v1/doctors/<id>/  → update profile (own doctor or admin)
    """
    queryset = DoctorProfile.objects.select_related("user", "specialization").prefetch_related("availability")
    permission_classes = [IsOwnerOrAdminOrReadOnly]

    def get_serializer_class(self):
        if self.request.method == "GET":
            return DoctorProfileSerializer
        return DoctorProfileSerializer

    def get_permissions(self):
        if self.request.method in ["GET"]:
            return [AllowAny()]
        return [IsAuthenticated(), IsOwnerOrAdminOrReadOnly()]


# ── AVAILABLE SLOTS ───────────────────────────────────────────
class DoctorAvailableSlotsView(APIView):
    """
    GET /api/v1/doctors/<id>/slots/?date=2026-03-15
    Returns all time slots for a doctor on a given date,
    with 'available: true/false' for each slot.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            doctor = DoctorProfile.objects.get(pk=pk, user__is_active=True)
        except DoctorProfile.DoesNotExist:
            return Response(
                {"error": "Doctor not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = AvailableSlotsSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        slots = serializer.get_slots(doctor)

        return Response({
            "success": True,
            "data": {
                "doctor_id": pk,
                "date": serializer.validated_data["date"],
                "slots": slots,
            }
        })


# ── DOCTOR AVAILABILITY (schedule management) ─────────────────
class DoctorAvailabilityView(generics.ListCreateAPIView):
    """
    GET  /api/v1/doctors/<id>/availability/  → view schedule
    POST /api/v1/doctors/<id>/availability/  → add a day (doctor or admin)
    """
    serializer_class = DoctorAvailabilitySerializer

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated(), IsDoctor()]

    def get_queryset(self):
        return DoctorAvailability.objects.filter(
            doctor_id=self.kwargs["pk"]
        )

    def perform_create(self, serializer):
        doctor = DoctorProfile.objects.get(pk=self.kwargs["pk"])
        serializer.save(doctor=doctor)


class DoctorAvailabilityDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    PATCH  /api/v1/doctors/<id>/availability/<avail_id>/
    DELETE /api/v1/doctors/<id>/availability/<avail_id>/
    """
    serializer_class = DoctorAvailabilitySerializer
    permission_classes = [IsAuthenticated, IsDoctor]

    def get_queryset(self):
        return DoctorAvailability.objects.filter(
            doctor_id=self.kwargs["pk"]
        )
