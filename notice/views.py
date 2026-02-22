


from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import Notice
from .serializers import NoticeSerializer
from rest_framework.permissions import AllowAny


class NoticeViewSet(ModelViewSet):
    serializer_class = NoticeSerializer
    queryset = Notice.objects.all()
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def get_queryset(self):
        """
        Filter notices for admin/center users.
        """
        user = self.request.user
        if user.is_authenticated:
            role = getattr(user.profile, "role", "")
            if role == "CENTER":
                return Notice.objects.filter(center=user.profile.center)
            return Notice.objects.all()
        return Notice.objects.filter(is_active=True)

    