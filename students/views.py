
# Django ORM & DB utilities
from django.db.models import Q, F, Count, Case, When, Value, CharField, Max
from django.db.models.functions import Coalesce
from django.db import transaction

# DRF imports
from rest_framework import viewsets, filters, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination

# Django Filter
from django_filters.rest_framework import DjangoFilterBackend

# Utilities
from datetime import datetime
import re
from num2words import num2words

# Local app imports
from .models import Student
from .serializers import (
    StudentSerializer,
    StudentResultSerializer,
    AdmitCardSerializer,
    MarksheetSerializer,
    MeritListSerializer,
    LifafaSerializer
)
from .pagination import MeritPagination, StandardResultsSetPagination



MONTH_MAP = {
    "JAN": "01", "FEB": "02", "MAR": "03", "APR": "04",
    "MAY": "05", "JUN": "06", "JUL": "07", "AUG": "08",
    "SEP": "09", "OCT": "10", "NOV": "11", "DEC": "12",
    }

def normalize_enroll_no(enroll_no):
    if not enroll_no:
        return enroll_no

    enroll_no = enroll_no.strip().upper()

    # Replace month names with numbers
    for month, number in MONTH_MAP.items():
        enroll_no = enroll_no.replace(month, number)

    # Remove all non-digits
    enroll_no = re.sub(r"\D", "", enroll_no)

    return enroll_no


CLASS_PROMOTION_MAP = {
    "IBTIDAI SAAL AWWAL": "IBTIDAI SAAL DOAM",
    "IBTIDAI SAAL DOAM": "SANVIYA SAAL AWWAL",
    "SANVIYA SAAL AWWAL": "SANVIYA SAAL DOAM",
    "SANVIYA SAAL DOAM": "ALIYA SAAL AWWAL",
    "ALIYA SAAL AWWAL": "ALIYA SAAL DOAM",
    "ALIYA SAAL DOAM": None,
}

def normalize_class_name(class_name):
    if not class_name:
        return None
    return class_name.replace("_", " ").upper()

# ================= Pagination =================
class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'limit'
    max_page_size = 300


class StudentViewSet(viewsets.ModelViewSet):
    serializer_class = StudentSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['session', 'student_class']
    search_fields = [
        'student_name', 'student_id', 'roll_no', 'enroll_no', 
        'father_husband_name', 'student_class', 'session',
        'medium', 'city', 'place', 'center__center_name'
    ]

    # ================= GET QUERYSET =================
    def get_queryset(self):
        # ⚡ Prevent swagger from crashing
        if getattr(self, 'swagger_fake_view', False):
            return Student.objects.none()

        user = self.request.user

        # ⚡ Anonymous users return empty
        if not user.is_authenticated:
            return Student.objects.none()

        # Base queryset
        queryset = Student.objects.all().order_by("id")

        # 🔒 Staff restriction
        if getattr(user, "role", None) == "staff":
            center = getattr(user, "center", None)
            if not center:
                return Student.objects.none()
            queryset = queryset.filter(center=center)

        # Query param filters
        session = self.request.query_params.get("session")
        student_class = self.request.query_params.get("student_class")
        search = self.request.query_params.get("search")
        student_id = self.request.query_params.get("student_id")
        global_search = self.request.query_params.get("global")
        
        # ================= EXACT STUDENT ID FILTER =================
        if student_id:
            queryset = queryset.filter(
                student_id__iexact=student_id.strip()
            )

        
        # ================= GLOBAL SEARCH BLOCK =================
        if search and global_search:  
            search = search.strip()

            return queryset.filter(
                Q(student_id__iexact=search) |
                Q(enroll_no__iexact=search) |
                Q(roll_no__iexact=search) |
                Q(student_name__icontains=search) |
                Q(student_class__iexact=search) |
                Q(session__iexact=search)
            ).order_by("-session")
            
        if session:
            queryset = queryset.filter(session=session)

        if student_class and student_class != "ALL":
            queryset = queryset.filter(student_class=student_class)

    
        if search:
            search = search.strip()

            # 🔥 First try full phrase match
            full_match = queryset.filter(
                Q(student_name__icontains=search)
            )

            if full_match.exists():
                return full_match.order_by("-id")

            words = search.strip().split()
            
            for word in words:
                queryset = queryset.filter(
                    Q(student_name__icontains=word)
                    | Q(student_id__iexact=word)
                    | Q(roll_no__icontains=word)
                    | Q(enroll_no__icontains=word)
                    | Q(father_husband_name__icontains=word)
                    | Q(student_class__icontains=word)
                    | Q(session__icontains=word)
                    | Q(medium__icontains=word)
                    | Q(city__icontains=word)
                    | Q(place__icontains=word)
                    | Q(center__center_name__icontains=word)
                )
                
        return queryset.order_by("-id")
    
    
    @action(detail=True, methods=["post"])
    def promote(self, request, pk=None):

        selected_student = self.get_object()

        # Always get latest session record
        student = (
            Student.objects
            .filter(student_id=selected_student.student_id)
            .order_by("-session")
            .first()
        )

        if not student:
            return Response(
                {"error": "Student not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        if student.result != "Pass":
            return Response(
                {"error": "Only passed students can be promoted."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Normalize class (handles underscore/space issue)
        current_class = student.student_class.replace("_", " ").upper()
        next_class = CLASS_PROMOTION_MAP.get(current_class)

        if not next_class:
            return Response(
                {"error": "Student is already in final class."},
                status=status.HTTP_400_BAD_REQUEST
            )

        next_session = request.data.get("session")

        if not next_session:
            from datetime import datetime
            next_session = str(datetime.now().year)

        if int(next_session) <= int(student.session):
            return Response(
                {"error": "Next session must be greater than current session."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if Student.objects.filter(
            student_id=student.student_id,
            session=next_session
        ).exists():
            return Response(
                {"error": "Student already promoted to this session."},
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            Student.objects.create(
                student_id=student.student_id,  
                enroll_no=student.enroll_no, 
                student_name=student.student_name,
                father_husband_name=student.father_husband_name,
                student_class=next_class,
                session=next_session,
                medium=student.medium,
                city=student.city,
                center=student.center,
                gender=student.gender,
                place=student.place,
            )

        return Response(
            {"message": f"Student promoted to {next_class} ({next_session}) successfully."},
            status=status.HTTP_201_CREATED
        )

        
    
    @action(detail=False, methods=["get"], url_path="generate-ids")
    def generate_ids(self, request):
        year_suffix = datetime.now().year % 100  # 2026 → 26

        # ---------- STUDENT ID PREVIEW ----------
        last_student = Student.objects.filter(student_id__startswith="JIB").order_by("-id").first()
        if last_student and last_student.student_id[3:].isdigit():
            last_number = int(last_student.student_id[3:])
        else:
            last_number = 79999
        preview_student_id = f"JIB{last_number + 1:05d}"

        # ---------- ROLL NO PREVIEW ----------
        last_roll = Student.objects.exclude(roll_no__isnull=True).order_by("-id").values_list("roll_no", flat=True).first()
        if last_roll and str(last_roll).isdigit():
            preview_roll_no = str(int(last_roll) + 1).zfill(6)
        else:
            preview_roll_no = "100000"

        # ---------- ENROLL NO PREVIEW ----------
        last_enroll = Student.objects.exclude(enroll_no__isnull=True).order_by("-id").values_list("enroll_no", flat=True).first()
        if last_enroll and "/" in last_enroll and last_enroll.split("/")[0].isdigit():
            last_num = int(last_enroll.split("/")[0])
        else:
            last_num = 100000
        preview_enroll_no = f"{last_num + 1:06d}/{year_suffix}"

        return Response({
            "student_id": preview_student_id,
            "roll_no": preview_roll_no,
            "enroll_no": preview_enroll_no,
            "note": "Preview only. Final values assigned on save.",
        })


    # ================= PERFORM CREATE =================
    def perform_create(self, serializer):
        user = self.request.user
        if getattr(user, "role", None) == "staff":
            serializer.save(center=getattr(user, "center", None))
        else:
            serializer.save()
    
   
    # ================= TOGGLE PUBLISH =================
    @action(detail=True, methods=["post"])
    def toggle_publish(self, request, pk=None):
        student = self.get_object()
        student.is_published = not student.is_published
        student.save()
        return Response({
            "message": "Publish status updated",
            "is_published": student.is_published
        })

    # ================= BULK PUBLISH =================
    @action(detail=False, methods=["post"])
    def bulk_publish(self, request):
        student_class = request.data.get("student_class")
        session = request.data.get("session")
        publish = request.data.get("publish", True)

        if not student_class or not session:
            return Response(
                {"error": "student_class and session are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        qs = Student.objects.filter(student_class=student_class, session=session)
        updated_count = qs.update(is_published=publish)

        return Response({
            "message": "Bulk publish updated successfully",
            "updated": updated_count
        })
        
    @action(detail=True, methods=["post"])
    def toggle_admit_publish(self, request, pk=None):
        student = self.get_object()
        student.is_admit_card_published = not student.is_admit_card_published
        student.save()

        return Response({
            "message": "Admit publish status updated",
            "is_admit_published": student.is_admit_card_published
        })

    # ================= BULK ADMIT CARD PUBLISH =================
    @action(detail=False, methods=["post"])
    def bulk_admit_publish(self, request):
        student_class = request.data.get("student_class")
        session = request.data.get("session")
        publish = request.data.get("publish", True)

        if not student_class or not session:
            return Response(
                {"error": "student_class and session are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        qs = Student.objects.filter(student_class=student_class, session=session)
        updated_count = qs.update(is_admit_card_published=publish)

        return Response({
            "message": "Bulk admit card updated successfully",
            "updated": updated_count
        })

    
    @action(detail=False, methods=["get"], url_path="summary")
    def summary(self, request):
        user = request.user
        qs = self.get_queryset()

        # Only published for non admin/staff
        if getattr(user, "role", None) not in ["admin", "staff"]:
            qs = qs.filter(is_published=True)

        session = request.query_params.get("session")
        gender = request.query_params.get("gender")  # gender filter

        if session:
            qs = qs.filter(session=session)

        if gender:
            qs = qs.filter(gender__iexact=gender)

        # ================= OVERALL =================
        total = qs.count()
        absent = qs.filter(grand_total=0).count()
        present = total - absent

        pass_count = qs.filter(result__iexact="Pass").count()
        fail_count = qs.filter(result__iexact="Fail").count()
        supplie_count = qs.filter(result__iexact="Supplie").count()

        overall = {
            "total": total,
            "present": present,
            "absent": absent,
            "pass": pass_count,
            "fail": fail_count,
            "suppli": supplie_count,
            "first_division": qs.filter(division="First Division").count(),
            "second_division": qs.filter(division="Second Division").count(),
            "third_division": qs.filter(division="Third Division").count(),
        }

        # ================= CLASS GROUPS =================
        CLASS_GROUPS = [
            ("IBTIDAIYA SAAL AWWAL", ["IBTIDAI SAAL AWWAL","IBTIDAI_SAAL_AWWAL"]),
            ("IBTIDAIYA SAAL DOWM", ["IBTIDAI SAAL DOAM", "IBTIDAI_SAAL_DOAM"]),
            ("SANIYA SAAL AWWAL", ["SANVIYA SAAL AWWAL", "SANVIYA_SAAL_AWWAL"]),
            ("SANIYA SAAL DOWM", ["SANVIYA SAAL DOAM", "SANVIYA_SAAL_DOAM"]),
            ("ALIYA SAAL AWWAL", ["ALIYA SAAL AWWAL", "ALIYA_SAAL_AWWAL"]),
            ("ALIYA SAAL DOWM", ["ALIYA SAAL DOAM", "ALIYA_SAAL_DOAM"]),
        ]

        class_summary = []
        for title, values in CLASS_GROUPS:
            # Filter students matching any of the class identifiers
            condition = Q()
            for value in values:
                condition |= Q(student_class__iexact=value)
            cqs = qs.filter(condition)

            total_cls = cqs.count()
            absent_cls = cqs.filter(grand_total=0).count()
            present_cls = total_cls - absent_cls
            pass_cls = cqs.filter(result__iexact="Pass").count()
            fail_cls = cqs.filter(result__iexact="Fail").count()
            supplie_cls = cqs.filter(result__iexact="Supplie").count()

            class_summary.append({
                "title": title,
                "total": total_cls,
                "present": present_cls,
                "absent": absent_cls,
                "pass": pass_cls,
                "fail": fail_cls,
                "suppli": supplie_cls,
                "first": cqs.filter(division="First Division").count(),
                "second": cqs.filter(division="Second Division").count(),
                "third": cqs.filter(division="Third Division").count(),
            })

        return Response({
            "overall": overall,
            "classes": class_summary
        })

    def create(self, request, *args, **kwargs):
        print("\n========== STUDENT CREATE DEBUG ==========")
        print("RAW REQUEST DATA:")
        print(request.data)

        serializer = self.get_serializer(data=request.data)

        if not serializer.is_valid():
            print("\n❌ SERIALIZER ERRORS:")
            print(serializer.errors)
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            self.perform_create(serializer)
        except Exception as e:
            print("\n❌ SAVE EXCEPTION:")
            print(str(e))
            raise

        print("\n✅ STUDENT CREATED SUCCESSFULLY")
        return Response(serializer.data, status=status.HTTP_201_CREATED)
        
    
    @action(detail=False, methods=["get"], url_path="reports")
    def reports(self, request):
        report_type = request.query_params.get("type")
        session = request.query_params.get("session")
        student_class = request.query_params.get("student_class")
        value = request.query_params.get("value")

        # ---------------- REQUIRED PARAMS ----------------
        if not report_type or not session:
            return Response(
                {"error": "type and session are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ---------------- BASE QUERYSET ----------------
        base_qs = self.get_queryset().filter(session=session)
        if student_class and student_class.upper() != "ALL":
            base_qs = base_qs.filter(student_class=student_class)

        # ---------------- FILTERED QUERYSET ----------------
        # Annotate admission_type so it's always available
        qs = base_qs.annotate(
            admission_type=Case(
                When(is_admit_card_published=True, then=Value("ADMITTED")),
                When(is_admit_card_published=False, then=Value("NOT ADMITTED")),
                default=Value("UNKNOWN"),
                output_field=CharField(),
            )
        )

        # ---------------- APPLY FILTERS ----------------
        if report_type == "gender" and value:
            qs = qs.filter(gender=value)
        elif report_type == "admission" and value:
            qs = qs.filter(admission_type=value)
        elif report_type == "result" and value:
            qs = qs.filter(result=value)
        elif report_type == "percentage" and value:
            try:
                min_p, max_p = map(float, value.split("-"))
                qs = qs.filter(avg_percentage__gte=min_p, avg_percentage__lte=max_p)
            except Exception:
                pass
        elif report_type == "division" and value:
            qs = qs.filter(division=value)
        elif report_type == "center" and value:
            qs = qs.filter(center__center_id=value)
        elif report_type == "medium" and value:
            qs = qs.filter(medium=value)

        # ---------------- BUILD SUMMARY ----------------
        summary = {}

        def build_summary(field_name):
            return qs.values(field_name).annotate(count=Count("id")).order_by(field_name)

        if report_type == "gender":
            summary = {row["gender"] or "OTHER": row["count"] for row in build_summary("gender")}
        elif report_type == "result":
            summary = {row["result"] or "UNKNOWN": row["count"] for row in build_summary("result")}
        elif report_type == "division":
            summary = {row["division"] or "NA": row["count"] for row in build_summary("division")}
        elif report_type == "medium":
            summary = {row["medium"] or "NA": row["count"] for row in build_summary("medium")}
        elif report_type == "class":
            summary = {row["student_class"] or "NA": row["count"] for row in build_summary("student_class")}
        elif report_type == "center":
            summary = {row["center__center_id"] or "NA": row["count"] for row in build_summary("center__center_id")}
        elif report_type == "admission":
            summary = {row["admission_type"] or "NA": row["count"] for row in build_summary("admission_type")}
        elif report_type == "percentage":
            # Optional: summary by range buckets
            summary = {}
        else:
            return Response({"error": "Invalid report type"}, status=status.HTTP_400_BAD_REQUEST)

        # ---------------- SERIALIZER ----------------
        serializer = self.get_serializer(qs, many=True)

        # ---------------- RESPONSE ----------------
        return Response(
            {
                "results": serializer.data,
                "total": qs.count(),
                "grand_total": base_qs.count(),
                "summary": summary,
                "report_type": report_type,
            },
            status=status.HTTP_200_OK,
        )




    
    # ================= LIST & CREATE OVERRIDES =================
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    
    @action(detail=True, methods=["get"], url_path="download-official-marksheet")
    def download_official_marksheet(self, request, pk=None):
        student = self.get_object()

        buffer = generate_official_marksheet(student)
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="Marksheet_{student.roll_no}.pdf"'
        return response


# ================= Student Result View =================
class StudentResultView(APIView):
    """
    Get a student's published result by roll_no + center_code
    """
    def get(self, request):
        roll_no = request.query_params.get("roll_no")
        center_code = request.query_params.get("center_code")

        if not roll_no or not center_code:
            return Response(
                {"message": "Roll No and Center Code required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            student = Student.objects.get(
                roll_no=roll_no,
                center__center_id=center_code,
                is_published=True
            )
        except Student.DoesNotExist:
            return Response(
                {"message": "Result not published yet"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = StudentResultSerializer(student)
        return Response(serializer.data)


# ================= Student Admit Card View =================
class StudentAdmitCardView(APIView):
    permission_classes = [AllowAny]
    
    """
    Get a student's published admit card by center_id + roll_no + session
    """
    def post(self, request):
        center_id = request.data.get("center_id")
        roll_no = request.data.get("roll_no")
        session = request.data.get("session")

        if not all([center_id, roll_no, session]):
            return Response(
                {"error": "Center ID, Roll No and Session are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        student = Student.objects.filter(
            center__center_id=center_id,
            roll_no=roll_no,
            session=session,
            is_admit_card_published=True
        ).first()

        if not student:
            return Response(
                {"error": "Admit card not found or not published"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = AdmitCardSerializer(student)
        return Response(serializer.data)




class PrintLifafa(APIView):
    def get(self, request, roll_no):
        student = Student.objects.filter(roll_no=roll_no).first()
        if not student:
            return Response({"error": "Student not found"}, status=404)

        return Response(LifafaSerializer(student).data)



class PrintMarksheet(APIView):
    """
    Get a single student's published marksheet in JSON format.
    """

    def get(self, request):
        qs = Student.objects.select_related("center").all()

        # ---------------- PERMISSION LOGIC ----------------
        user = request.user
        if getattr(user, "role", None) not in ["admin", "staff"]:
            qs = qs.filter(is_published=True)

        # ---------------- QUERY PARAMS ----------------
        roll_no = request.query_params.get("roll_no")
        center_id = request.query_params.get("center_id")
        student_class = request.query_params.get("student_class")
        session = request.query_params.get("session")

        # ---------------- FILTERS ----------------
        if roll_no:
            qs = qs.filter(roll_no__iexact=roll_no.strip())

        if center_id:
            qs = qs.filter(center__center_id__iexact=center_id.strip())

        if student_class:
            qs = qs.filter(student_class__iexact=student_class.strip())

        if session:
            qs = qs.filter(session__iexact=session.strip())

        student = qs.first()

        if not student:
            return Response(
                {"error": "Marksheet not found or not published"},
                status=status.HTTP_404_NOT_FOUND
            )

        # ---------------- MARKS ARRAY ----------------
        marks = []
        for i, paper in enumerate(
            [student.paper1, student.paper2, student.paper3, student.paper4],
            start=1
        ):
            marks.append({
                "subject": f"Paper {i}",
                "max_marks": 100,
                "min_marks": 33,
                "marks": paper if paper is not None else 0,
            })

        # ---------------- SERIALIZE ----------------
        serializer = MarksheetSerializer(student)
        data = serializer.data

        data["marks"] = marks
        data["total_words"] = (
            num2words(student.total).title()
            if student.total is not None
            else "Zero"
        )

        return Response(data, status=status.HTTP_200_OK)
    


class MeritList(APIView):
    serializer_class = MeritListSerializer
    pagination_class = MeritPagination

    def get(self, request):
        session = request.query_params.get("session")
        student_class = request.query_params.get("student_class")

        if not session:
            return Response({"error": "session required"}, status=400)

        # ✅ treat session as string (important)
        current_year = session.strip()
        previous_year = str(int(current_year) - 1)

        # 🔹 Step 1: Current session students
        current_students = Student.objects.select_related("center").filter(
            session=current_year
        )

        if student_class:
            normalized_class = student_class.replace("_", " ")
            current_students = current_students.filter(
                Q(student_class=student_class) |
                Q(student_class=normalized_class)
            )

        if not current_students.exists():
            paginator = self.pagination_class()
            page = paginator.paginate_queryset([], request, view=self)
            return paginator.get_paginated_response([])

        student_ids = current_students.values_list("student_id", flat=True)

        # 🔹 Step 2: Fetch both sessions for those students
        qs = Student.objects.select_related("center").filter(
            student_id__in=student_ids,
            session__in=[previous_year, current_year]
        )

        results_map = {}

        # 🔹 Step 3: Combine marks
        for s in qs:
            key = s.student_id

            if key not in results_map:
                results_map[key] = {
                    "roll_no": s.roll_no,
                    "enroll_no": s.enroll_no,
                    "center_id": s.center.center_id if s.center else "",
                    "student_name": s.student_name,
                    "previous": 0,
                    "current": 0,
                }

            total = sum([
                s.paper1 or 0,
                s.paper2 or 0,
                s.paper3 or 0,
                s.paper4 or 0,
            ])

            if str(s.session) == previous_year:
                results_map[key]["previous"] += total

            if str(s.session) == current_year:
                results_map[key]["current"] += total

        # 🔹 Step 4: Final list
        results = []

        for data in results_map.values():
            data["two_year_total"] = data["previous"] + data["current"]
            results.append(data)

        # 🔹 Sort
        results.sort(key=lambda x: x["two_year_total"], reverse=True)

        # 🔹 Ranking
        last_score = None
        rank = 0

        for index, item in enumerate(results, start=1):
            if item["two_year_total"] != last_score:
                rank = index
                last_score = item["two_year_total"]

            item["rank"] = rank

        # 🔹 Pagination
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(results, request, view=self)

        if page is not None:
            serializer = self.serializer_class(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = self.serializer_class(results, many=True)
        return Response(serializer.data)
