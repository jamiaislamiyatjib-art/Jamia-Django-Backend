

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

from django.db.models import Count

from academics.models import ExamTimeTable





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
        ).filter(
            has_students=True
        )

        # ✅ THIS IS REQUIRED FOR SEARCH TO WORK
        queryset = self.filter_queryset(queryset)

        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)

        return Response(serializer.data)
    
    
# =========================
# CLASS NORMALIZER
# =========================
def normalize_class_name(value):

    if not value:
        return ""

    value = str(value).upper().strip()

    replacements = {

        "FIRST": "1",
        "FIRST CLASS": "1",
        "CLASS 1": "1",

        "SECOND": "2",
        "SECOND CLASS": "2",
        "CLASS 2": "2",

        "THIRD": "3",
        "THIRD CLASS": "3",
        "CLASS 3": "3",

        "FOURTH": "4",
        "FOURTH CLASS": "4",
        "CLASS 4": "4",

    }

    return replacements.get(value, value)



class LifafaViewSet(viewsets.ReadOnlyModelViewSet):

    queryset = Lifafa.objects.all()

    serializer_class = LifafaSerializer

    pagination_class = None


    # =========================
    # FILTER LIFAFA
    # =========================
    def get_queryset(self):

        queryset = (
            Lifafa.objects
            .select_related("center")
            .prefetch_related("papers")
        )


        center_id = self.request.query_params.get(
            "center_id"
        )

        session = self.request.query_params.get(
            "session"
        )


        if center_id:

            queryset = queryset.filter(
                center_id=center_id
            )


        if session and session != "all":

            queryset = queryset.filter(
                session=session
            )


        return queryset



    # =========================
    # LIFAFA STATS API
    # =========================
    @action(
        detail=False,
        methods=["get"]
    )
    def stats(self, request):

        center_id = request.GET.get(
            "center_id"
        )

        session = request.GET.get(
            "session"
        )


        if not center_id:

            return Response(
                {
                    "error":
                    "center_id required"
                },
                status=400
            )


        lifafas = (
            Lifafa.objects
            .select_related("center")
            .prefetch_related("papers")
            .filter(
                center_id=center_id
            )
        )


        if session and session != "all":

            lifafas = lifafas.filter(
                session=session
            )


        result = []


        for lifafa in lifafas:


            # =====================================
            # GET EXAM DATE FROM EXAM TIME TABLE
            # =====================================

            exam_date = (
                ExamTimeTable.objects
                .filter(
                    center=lifafa.center
                )
                .order_by(
                    "exam_date"
                )
                .values_list(
                    "exam_date",
                    flat=True
                )
                .first()
            )



            if not exam_date:
                continue



            # =========================
            # STUDENT COUNT
            # =========================

            students = Student.objects.filter(

                center_id=center_id,

                session=lifafa.session

            ).only(
                "student_class",
                "medium"
            )



            stats = (

                students

                .values(
                    "student_class",
                    "medium"
                )

                .annotate(
                    count=Count("id")
                )

            )



            stats_dict = {}



            for row in stats:


                class_name = normalize_class_name(
                    row["student_class"]
                )


                medium = (
                    row["medium"] or ""
                ).lower().strip()



                if class_name not in stats_dict:

                    stats_dict[class_name] = {

                        "total":0,
                        "urdu":0,
                        "hindi":0

                    }



                stats_dict[class_name]["total"] += (
                    row["count"]
                )



                if medium == "urdu":

                    stats_dict[class_name]["urdu"] += (
                        row["count"]
                    )


                elif medium == "hindi":

                    stats_dict[class_name]["hindi"] += (
                        row["count"]
                    )




            papers = []


            total_urdu = 0

            total_hindi = 0

            total_students = 0




            for paper in lifafa.papers.all().order_by(
                "paper_no"
            ):


                normalized = normalize_class_name(
                    paper.exam_name
                )



                stat = stats_dict.get(

                    normalized,

                    {
                        "total":0,
                        "urdu":0,
                        "hindi":0
                    }

                )
                papers.append({

                    "exam_name":
                        paper.exam_name,

                    "paper_no":
                        paper.paper_no,

                    "total":
                        stat["total"],

                    "urdu":
                        stat["urdu"],

                    "hindi":
                        stat["hindi"]

                })

                total_urdu += stat["urdu"]

                total_hindi += stat["hindi"]

                total_students += stat["total"]

            result.append({

                "id":
                    lifafa.id,

                "center":
                    lifafa.center.center_name,

                "center_id":
                    lifafa.center.center_id,

                # NOW COMING FROM EXAM TIME TABLE
                "exam_date":
                    exam_date,


                "session":
                    lifafa.session,


                "session_display":
                    lifafa.get_session_display(),



                "papers":
                    papers,



                "total_urdu":
                    total_urdu,


                "total_hindi":
                    total_hindi,


                "total_students":
                    total_students

            })



        return Response(result)