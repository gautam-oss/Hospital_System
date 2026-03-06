"""
NOTIFICATION SERVICE

Handles all email notifications triggered by appointment events.
In dev: emails print to console.
In prod: sent via SMTP (configured in settings).

WHY a service module (not signals)?
Services are easier to test, easier to trace, and explicit.
Signals can cause mysterious side effects.
"""

import logging
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

logger = logging.getLogger(__name__)


def send_appointment_confirmation(appointment):
    """Sent to patient when appointment is booked."""
    try:
        subject = f"Appointment Confirmed — {appointment.appointment_date}"
        message = (
            f"Dear {appointment.patient.get_full_name()},\n\n"
            f"Your appointment has been booked.\n\n"
            f"Doctor: Dr. {appointment.doctor.user.get_full_name()}\n"
            f"Specialization: {appointment.doctor.specialization}\n"
            f"Date: {appointment.appointment_date}\n"
            f"Time: {appointment.appointment_time}\n\n"
            f"Please arrive 10 minutes early.\n\n"
            f"Hospital Appointment System"
        )
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[appointment.patient.email],
            fail_silently=False,
        )
        logger.info(f"Confirmation email sent to {appointment.patient.email}")
    except Exception as e:
        logger.error(f"Failed to send confirmation email: {e}")


def send_appointment_cancellation(appointment):
    """Sent to both patient and doctor when appointment is cancelled."""
    try:
        subject = f"Appointment Cancelled — {appointment.appointment_date}"
        message = (
            f"Dear {appointment.patient.get_full_name()},\n\n"
            f"Your appointment with Dr. {appointment.doctor.user.get_full_name()} "
            f"on {appointment.appointment_date} at {appointment.appointment_time} "
            f"has been cancelled.\n\n"
        )
        if appointment.cancellation_reason:
            message += f"Reason: {appointment.cancellation_reason}\n\n"

        message += "Please book a new appointment if needed.\n\nHospital Appointment System"

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[
                appointment.patient.email,
                appointment.doctor.user.email,
            ],
            fail_silently=False,
        )
        logger.info(f"Cancellation email sent for appointment {appointment.id}")
    except Exception as e:
        logger.error(f"Failed to send cancellation email: {e}")


def send_appointment_reminder(appointment):
    """Sent 24 hours before the appointment (called by a scheduled task)."""
    try:
        subject = f"Reminder: Appointment Tomorrow at {appointment.appointment_time}"
        message = (
            f"Dear {appointment.patient.get_full_name()},\n\n"
            f"This is a reminder of your appointment tomorrow.\n\n"
            f"Doctor: Dr. {appointment.doctor.user.get_full_name()}\n"
            f"Date: {appointment.appointment_date}\n"
            f"Time: {appointment.appointment_time}\n\n"
            f"Hospital Appointment System"
        )
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[appointment.patient.email],
            fail_silently=False,
        )
        logger.info(f"Reminder email sent to {appointment.patient.email}")
    except Exception as e:
        logger.error(f"Failed to send reminder email: {e}")
