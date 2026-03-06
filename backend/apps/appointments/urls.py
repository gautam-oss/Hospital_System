from django.urls import path
from .views import (
    AppointmentListCreateView,
    AppointmentDetailView,
    AdminAppointmentStatsView,
)

urlpatterns = [
    path("", AppointmentListCreateView.as_view(), name="appointment-list"),
    path("<int:pk>/", AppointmentDetailView.as_view(), name="appointment-detail"),
    path("admin/stats/", AdminAppointmentStatsView.as_view(), name="appointment-stats"),
]
