    
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import Notice
from .serializers import NoticeSerializer


class NoticeViewSet(ModelViewSet):
    serializer_class = NoticeSerializer
    queryset = Notice.objects.all()
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        """
        Save created_by only if user is authenticated.
        Prevent error when anonymous/public user creates notice.
        """
        if self.request.user.is_authenticated:
            serializer.save(created_by=self.request.user)
        else:
            serializer.save()

    def get_queryset(self):
        """
        - Admin/staff -> all notices
        - Center user -> only their center notices
        - Public/student -> only active notices
        """
        user = self.request.user

        if user.is_authenticated:
            profile = getattr(user, "profile", None)
            role = getattr(profile, "role", "")

            if role == "CENTER":
                center = getattr(profile, "center", None)
                if center:
                    return Notice.objects.filter(center=center).order_by("-created_at")
                return Notice.objects.none()

            return Notice.objects.all().order_by("-created_at")

        return Notice.objects.filter(is_active=True).order_by("-created_at")

    @action(detail=False, methods=["get"], url_path="student_notices")
    def student_notices(self, request):
        """
        Public/student notices endpoint
        Supports:
        /notices/student_notices/
        /notices/student_notices/?center=3
        """
        queryset = Notice.objects.filter(is_active=True).order_by("-created_at")

        center_id = request.query_params.get("center")
        if center_id:
            queryset = queryset.filter(center_id=center_id)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)