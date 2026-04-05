

from rest_framework.viewsets import ModelViewSet
from rest_framework.filters import SearchFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import AllowAny
from rest_framework.decorators import action

from .models import Center, Lifafa
from .serializers import CenterSerializer, LifafaSerializer
from .pagination import CenterPagination

from rest_framework import viewsets

from datetime import datetime
from django.db.models import Exists, OuterRef

from students.models import Student   

from rest_framework.decorators import api_view
from rest_framework.response import Response
from students.models import Student
from .models import Lifafa


class CenterViewSet(ModelViewSet):

    queryset = Center.objects.all().prefetch_related("mobile_numbers", "emails")
    serializer_class = CenterSerializer
    pagination_class = CenterPagination
    permission_classes = [AllowAny]

    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['state', 'city']

    search_fields = [
        'center_name',
        'center_id',
        'city',
        'state',
        'pincode',
        'mobile_numbers__mobile',
        'emails__email',
    ]

    @action(detail=False, methods=["get"], url_path="current-year")
    def current_year(self, request):

        year = str(datetime.now().year) 

        student_subquery = Student.objects.filter(
            center_id=OuterRef("center_id"),
            session=year
        )

        queryset = self.get_queryset().annotate(
            has_students=Exists(student_subquery)
        ).filter(has_students=True)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    


class LifafaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Lifafa.objects.all()
    serializer_class = LifafaSerializer
    pagination_class = None  # IMPORTANT FOR PRINT

    # =========================
    # FILTER LIFAFA
    # =========================
    def get_queryset(self):

        queryset = Lifafa.objects.select_related("center").prefetch_related("papers")

        center_id = self.request.query_params.get("center_id")
        session = self.request.query_params.get("session")

        print("CENTER:", center_id)
        print("SESSION:", session)

        if center_id:
            queryset = queryset.filter(center_id=center_id)

        if session and session != "all":
            queryset = queryset.filter(session=session)

        print("RESULT COUNT:", queryset.count())

        return queryset

    # =========================
    # LIFAFA STATS API
    # =========================
    @action(detail=False, methods=["get"])
    def stats(self, request):

        center_id = request.GET.get("center_id")
        session = request.GET.get("session")

        if not center_id:
            return Response({"error": "center_id required"}, status=400)

        lifafas = Lifafa.objects.filter(center_id=center_id)

        if session and session != "all":
            lifafas = lifafas.filter(session=session)

        print("========== LIFAFA DEBUG START ==========")
        print("Center:", center_id)
        print("Session:", session)

        result = []

        for lifafa in lifafas:

            exam_year = lifafa.exam_date.year if lifafa.exam_date else None

            print("\nLifafa ID:", lifafa.id)
            print("Exam Year:", exam_year)

            students = Student.objects.filter(
                center_id=center_id,
                session=str(exam_year)
            )

            print("Students count:", students.count())

            stats = (
                students
                .values("student_class", "medium")
                .annotate(count=Count("id"))
            )

            stats_dict = {}

            for row in stats:
                class_name = (row["student_class"] or "").upper().strip()
                medium = (row["medium"] or "").lower().strip()

                if class_name not in stats_dict:
                    stats_dict[class_name] = {
                        "total": 0,
                        "urdu": 0,
                        "hindi": 0
                    }

                stats_dict[class_name]["total"] += row["count"]

                if medium == "urdu":
                    stats_dict[class_name]["urdu"] += row["count"]

                elif medium == "hindi":
                    stats_dict[class_name]["hindi"] += row["count"]

            papers = []

            for paper in lifafa.papers.all():

                normalized = paper.exam_name.replace("-", " SAAL ").upper()

                stat = stats_dict.get(normalized, {
                    "total": 0,
                    "urdu": 0,
                    "hindi": 0
                })

                papers.append({
                    "exam_name": paper.exam_name,
                    "paper_no": paper.paper_no,
                    "total": stat["total"],
                    "urdu": stat["urdu"],
                    "hindi": stat["hindi"]
                })

            result.append({
                "id": lifafa.id,
                "center": lifafa.center.center_name,
                "center_id": lifafa.center.center_id,
                "exam_date": lifafa.exam_date,
                "session": lifafa.session,
                "session_display": lifafa.get_session_display(),
                "papers": papers
            })

        print("========== LIFAFA DEBUG END ==========")

        return Response(result)