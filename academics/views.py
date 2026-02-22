
from rest_framework.viewsets import ModelViewSet
from .models import Course, ExamTimeTable
from .serializers import CourseSerializer, ExamTimeTableSerializer
from rest_framework.exceptions import PermissionDenied

from rest_framework.permissions import IsAdminUser, AllowAny
from rest_framework.filters import SearchFilter
from django_filters.rest_framework import DjangoFilterBackend


from rest_framework import viewsets, filters, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from django_filters.rest_framework import DjangoFilterBackend

from .models import ExamTimeTable
from .serializers import ExamTimeTableSerializer


class CourseViewSet(ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer


class ExamTimeTableViewSet(viewsets.ModelViewSet):
    serializer_class = ExamTimeTableSerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ["paper", "classes"]
    filterset_fields = ["center", "exam_date"]

    def get_queryset(self):
        # ⚡ Prevent swagger crash
        if getattr(self, "swagger_fake_view", False):
            return ExamTimeTable.objects.none()

        queryset = ExamTimeTable.objects.all()
        user = self.request.user

        # 🔒 STAFF → ONLY THEIR CENTER
        if user.is_authenticated and getattr(user, "role", None) == "staff":
            center = getattr(user, "center", None)
            if center:
                queryset = queryset.filter(center=center)

        # ✅ FILTER BY QUERY PARAMS (optional)
        center_id = self.request.query_params.get("center")
        if center_id:
            queryset = queryset.filter(center_id=center_id)

        exam_date = self.request.query_params.get("exam_date")
        if exam_date:
            queryset = queryset.filter(exam_date=exam_date)

        return queryset

    def perform_create(self, serializer):
        user = self.request.user
        if not user.is_authenticated:
            raise PermissionDenied("Authentication required")

        if getattr(user, "role", None) == "staff":
            center = getattr(user, "center", None)
            if not center:
                raise PermissionDenied("Staff has no center assigned")
            serializer.save(center=center)

        elif getattr(user, "role", None) == "admin":
            if not serializer.validated_data.get("center"):
                raise PermissionDenied("Center is required for admin")
            serializer.save()

        else:
            raise PermissionDenied("Not allowed")

    def destroy(self, request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated or getattr(user, "role", None) != "admin":
            raise PermissionDenied("Only admin can delete exam timetable")
        return super().destroy(request, *args, **kwargs)
