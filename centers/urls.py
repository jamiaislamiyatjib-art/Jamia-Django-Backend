# from rest_framework.routers import DefaultRouter
# from .views import CenterViewSet

# router = DefaultRouter()
# router.register(r'centers', CenterViewSet, basename='centers')

# urlpatterns = router.urls


from rest_framework.routers import DefaultRouter
from .views import CenterViewSet, LifafaViewSet

router = DefaultRouter()
router.register(r'centers', CenterViewSet, basename='centers')
router.register(r'lifafas', LifafaViewSet, basename='lifafas')

urlpatterns = router.urls