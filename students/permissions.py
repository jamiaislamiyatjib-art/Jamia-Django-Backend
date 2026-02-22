

from rest_framework.permissions import BasePermission

class IsAdminOrCenter(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        profile = request.user.profile

        # Admin can access everything
        if profile.role == 'ADMIN':
            return True

        # Center staff can access only their own center
        if profile.role == 'CENTER':
            # Compare IDs to avoid object mismatch
            student_center_id = obj.center.id if hasattr(obj.center, "id") else obj.center
            user_center_id = profile.center.id if hasattr(profile.center, "id") else profile.center
            return student_center_id == user_center_id

        return False
