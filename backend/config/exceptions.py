"""
CUSTOM EXCEPTION HANDLER

WHY? DRF's default error format is inconsistent.
Sometimes it returns {"detail": "..."}, other times {"field": ["error"]}.

We standardize ALL error responses to:
{
    "success": false,
    "error": {
        "code": "validation_error",
        "message": "Human-readable message",
        "details": { ... }   ← field-level errors if applicable
    }
}

This makes the React frontend's error handling much simpler.
"""

import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    # First, let DRF handle the exception normally
    response = exception_handler(exc, context)

    if response is not None:
        error_data = {
            "success": False,
            "error": {
                "code": _get_error_code(response.status_code),
                "message": _get_error_message(response.data),
                "details": response.data if isinstance(response.data, dict) else {},
            },
        }
        response.data = error_data

    return response


def _get_error_code(status_code):
    codes = {
        400: "bad_request",
        401: "unauthorized",
        403: "forbidden",
        404: "not_found",
        405: "method_not_allowed",
        409: "conflict",
        429: "too_many_requests",
        500: "server_error",
    }
    return codes.get(status_code, "error")


def _get_error_message(data):
    if isinstance(data, dict):
        if "detail" in data:
            return str(data["detail"])
        # For validation errors, summarize the first field error
        for field, errors in data.items():
            if isinstance(errors, list) and errors:
                return f"{field}: {errors[0]}"
    if isinstance(data, list) and data:
        return str(data[0])
    return "An error occurred."
