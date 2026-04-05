
from rest_framework.viewsets import ModelViewSet
from .models import Course, ExamTimeTable
from .serializers import CourseSerializer, ExamTimeTableSerializer
from rest_framework.exceptions import PermissionDenied

from rest_framework.permissions import IsAdminUser, AllowAny
from rest_framework.filters import SearchFilter
from django_filters.rest_framework import DjangoFilterBackend


from rest_framework import viewsets, filters, status
from rest_framework.permissions import IsAuthenticated

from rest_framework.response import Response
from django.db.models import Q




class CourseViewSet(ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer




class ExamTimeTableViewSet(viewsets.ModelViewSet):
    serializer_class = ExamTimeTableSerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ["paper", "classes"]
    filterset_fields = ["center", "exam_date"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return ExamTimeTable.objects.none()

        queryset = ExamTimeTable.objects.all()
        user = self.request.user

        # Staff can see their center + global entries
        if user.is_authenticated and getattr(user, "role", None) == "staff":
            center = getattr(user, "center", None)
            if center:
                queryset = queryset.filter(Q(center=center) | Q(center__isnull=True))
        return queryset

    def perform_create(self, serializer):
        user = self.request.user
        role = getattr(user, "role", None)
        print("CREATE DEBUG: User:", user, "Role:", role)
        print("CREATE DEBUG: Payload:", self.request.data)

        if not user.is_authenticated:
            raise PermissionDenied("Authentication required")

        if role == "staff":
            if not user.center:
                raise PermissionDenied("Staff has no center assigned")
            serializer.save(center=user.center)  # assign instance
        elif role == "admin":
            serializer.save()  # admin can set center or null
        else:
            raise PermissionDenied("Not allowed")

    def perform_update(self, serializer):
        user = self.request.user
        role = getattr(user, "role", None)
        print("UPDATE DEBUG: User:", user, "Role:", role)
        print("UPDATE DEBUG: Payload:", self.request.data)

        if not user.is_authenticated:
            raise PermissionDenied("Authentication required")

        try:
            if role == "staff":
                serializer.save(center=user.center) 
            elif role == "admin":
                serializer.save()  
            else:
                raise PermissionDenied("Not allowed")
        except Exception as e:
            print("UPDATE ERROR:", e)
            print("Serializer errors:", serializer.errors)
            raise

    def destroy(self, request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated or getattr(user, "role", None) != "admin":
            raise PermissionDenied("Only admin can delete exam timetable")
        return super().destroy(request, *args, **kwargs)