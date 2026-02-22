from rest_framework.routers import DefaultRouter
from .views import CourseViewSet, ExamTimeTableViewSet

router = DefaultRouter()
router.register(r'courses', CourseViewSet, basename='courses')
router.register(r'exam-timetable', ExamTimeTableViewSet, basename='timetable')

urlpatterns = router.urls
