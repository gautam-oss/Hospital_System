from django.urls import path
from .views import (
    SpecializationListView,
    DoctorListView,
    DoctorDetailView,
    DoctorAvailableSlotsView,
    DoctorAvailabilityView,
    DoctorAvailabilityDetailView,
)

# All prefixed with /api/v1/doctors/ from root urls.py
urlpatterns = [
    path("", DoctorListView.as_view(), name="doctor-list"),
    path("<int:pk>/", DoctorDetailView.as_view(), name="doctor-detail"),
    path("<int:pk>/slots/", DoctorAvailableSlotsView.as_view(), name="doctor-slots"),
    path("<int:pk>/availability/", DoctorAvailabilityView.as_view(), name="doctor-availability"),
    path("<int:pk>/availability/<int:avail_id>/", DoctorAvailabilityDetailView.as_view(), name="doctor-availability-detail"),
    path("specializations/", SpecializationListView.as_view(), name="specialization-list"),
]
