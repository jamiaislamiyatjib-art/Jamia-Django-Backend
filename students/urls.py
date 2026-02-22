from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import StudentViewSet, StudentResultView, StudentAdmitCardView

router = DefaultRouter()
router.register(r'students', StudentViewSet, basename='students'),


urlpatterns = [
    path('', include(router.urls)),
    path("student-result/", StudentResultView.as_view(), name="student-result"),
    path("admit-card/", StudentAdmitCardView.as_view(), name="admit-card"),
]


from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    StudentViewSet,
    StudentResultView,
    StudentAdmitCardView,
    PrintMarksheet,
    MeritList,
    # SummaryReport,
    # StudentReportView,
    PrintLifafa,
)

router = DefaultRouter()
router.register(r"students", StudentViewSet, basename="students")

urlpatterns = [
    # ---------- CRUD + SEARCH ----------
    path("", include(router.urls)),

    # ---------- PUBLIC RESULT ----------
    path("student-result/", StudentResultView.as_view(), name="student-result"),
    path("admit-card/", StudentAdmitCardView.as_view(), name="admit-card"),

    # ---------- PRINT / REPORTS ----------
    # path("marksheet/<str:roll_no>/", PrintMarksheet.as_view(), name="print-marksheet"),
    path("print-marksheet/", PrintMarksheet.as_view(), name="print-marksheet"),
    


    path("merit-list/", MeritList.as_view(), name="merit-list"),
    # path("students/reports/", StudentReportView.as_view(), name="student-reports"),
    path("lifafa/<str:roll_no>/", PrintLifafa.as_view(), name="print-lifafa"),
]


