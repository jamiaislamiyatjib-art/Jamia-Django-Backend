from rest_framework.permissions import BasePermission

class IsAdminOrCenter(BasePermission):
   
    def has_permission(self, request, view):
        if request.user.is_authenticated:
            role = getattr(request.user.profile, "role", "")
            return role in ["ADMIN", "CENTER"]
        return False
