"""
PERMISSIONS — Role-Based Access Control (RBAC)

How DRF permissions work:
  1. Request hits the view
  2. DRF calls has_permission() on every permission class
  3. If ANY returns False → 403 Forbidden
  4. For object-level checks, has_object_permission() is called

We create custom classes so we can write clean, readable views:

  permission_classes = [IsAuthenticated, IsDoctor]
  # instead of: if request.user.role != 'doctor': raise PermissionDenied
"""

from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdmin(BasePermission):
    """Only admin users can access this endpoint."""
    message = "Access restricted to administrators."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.is_admin
        )


class IsDoctor(BasePermission):
    """Only doctor users can access this endpoint."""
    message = "Access restricted to doctors."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.is_doctor
        )


class IsPatient(BasePermission):
    """Only patient users can access this endpoint."""
    message = "Access restricted to patients."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.is_patient
        )


class IsAdminOrDoctor(BasePermission):
    """Admins and doctors can access this endpoint."""
    message = "Access restricted to administrators and doctors."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and (request.user.is_admin or request.user.is_doctor)
        )


class IsOwnerOrAdmin(BasePermission):
    """
    Object-level permission — only the owner of an object or an admin can access it.

    Example: patient can only view their OWN appointments.
    Usage: Add to permission_classes AND call self.check_object_permissions(request, obj) in view.
    """
    message = "You do not have permission to access this resource."

    def has_object_permission(self, request, view, obj):
        # Admins can access everything
        if request.user.is_admin:
            return True

        # Check if the object has a 'user' or 'patient' field pointing to the requester
        if hasattr(obj, "user"):
            return obj.user == request.user
        if hasattr(obj, "patient"):
            return obj.patient == request.user

        return False


class IsOwnerOrAdminOrReadOnly(BasePermission):
    """
    Read-only for authenticated users.
    Write access only for the owner or admin.

    Example: anyone can GET a doctor's profile,
    but only that doctor (or admin) can PATCH it.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True

        if request.user.is_admin:
            return True

        if hasattr(obj, "user"):
            return obj.user == request.user

        return obj == request.user
