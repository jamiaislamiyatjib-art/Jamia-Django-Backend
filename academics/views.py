
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

from django.db.models import Case, When, IntegerField, Value, Q
from django.db.models.functions import Lower, Trim

from rest_framework import viewsets, filters
from rest_framework.permissions import AllowAny
from rest_framework.exceptions import PermissionDenied

from django_filters.rest_framework import DjangoFilterBackend

from .models import ExamTimeTable
from .serializers import ExamTimeTableSerializer




class CourseViewSet(ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer


class ExamTimeTableViewSet(viewsets.ModelViewSet):

    serializer_class = ExamTimeTableSerializer
    permission_classes = [AllowAny]

    filter_backends = [
        filters.SearchFilter,
        DjangoFilterBackend
    ]

    search_fields = [
        "paper",
        "classes"
    ]

    filterset_fields = [
        "center",
        "exam_date"
    ]


    def get_queryset(self):

        if getattr(self, "swagger_fake_view", False):
            return ExamTimeTable.objects.none()


        queryset = ExamTimeTable.objects.all()


        # ==============================
        # PAPER ORDERING
        # ==============================
        queryset = queryset.annotate(

            paper_clean=Lower(
                Trim("paper")
            )

        ).annotate(

            paper_order=Case(

                When(
                    paper_clean="first paper",
                    then=Value(1)
                ),

                When(
                    paper_clean="second paper",
                    then=Value(2)
                ),

                When(
                    paper_clean="third paper",
                    then=Value(3)
                ),

                When(
                    paper_clean="fourth paper",
                    then=Value(4)
                ),

                default=Value(99),

                output_field=IntegerField()
            )

        ).order_by(
            "paper_order",
            "exam_date",
            "time"
        )


        # ==============================
        # STAFF CENTER FILTER
        # ==============================

        user = self.request.user


        if user.is_authenticated:

            role = getattr(user, "role", None)

            if role == "staff":

                center = getattr(user, "center", None)

                if center:

                    queryset = queryset.filter(
                        Q(center=center) |
                        Q(center__isnull=True)
                    )


        return queryset



    # ==============================
    # CREATE
    # ==============================

    def perform_create(self, serializer):

        user = self.request.user

        role = getattr(
            user,
            "role",
            None
        )


        print(
            "CREATE DEBUG:",
            user,
            role
        )

        print(
            "PAYLOAD:",
            self.request.data
        )


        if not user.is_authenticated:

            raise PermissionDenied(
                "Authentication required"
            )


        if role == "staff":

            if not user.center:

                raise PermissionDenied(
                    "Staff has no center assigned"
                )


            serializer.save(
                center=user.center
            )


        elif role == "admin":

            serializer.save()


        else:

            raise PermissionDenied(
                "Not allowed"
            )



    # ==============================
    # UPDATE
    # ==============================

    def perform_update(self, serializer):

        user = self.request.user

        role = getattr(
            user,
            "role",
            None
        )


        print(
            "UPDATE DEBUG:",
            user,
            role
        )

        print(
            "PAYLOAD:",
            self.request.data
        )


        if not user.is_authenticated:

            raise PermissionDenied(
                "Authentication required"
            )


        if role == "staff":

            serializer.save(
                center=user.center
            )


        elif role == "admin":

            serializer.save()


        else:

            raise PermissionDenied(
                "Not allowed"
            )



    # ==============================
    # DELETE
    # ==============================

    def destroy(
        self,
        request,
        *args,
        **kwargs
    ):

        user = request.user


        if (
            not user.is_authenticated
            or getattr(user, "role", None) != "admin"
        ):

            raise PermissionDenied(
                "Only admin can delete exam timetable"
            )


        return super().destroy(
            request,
            *args,
            **kwargs
        )