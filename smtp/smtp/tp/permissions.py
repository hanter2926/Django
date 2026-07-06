from rest_framework import permissions


class IsInstructorOrReadOnly(permissions.BasePermission):
    """Allow safe methods for everyone. Only users with role 'instructor' or 'admin' can unsafe methods."""

    def has_permission(self, request, view):
        # Allow read-only for any request
        if request.method in permissions.SAFE_METHODS:
            return True

        user = request.user
        if not user or not user.is_authenticated:
            return False

        # Admins and Instructors can modify
        role = getattr(user, 'role', None)
        return role in ('admin', 'instructor')
