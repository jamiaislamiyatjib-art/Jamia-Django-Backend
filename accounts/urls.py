# from django.urls import path
# from .views import RegisterView, MyTokenObtainPairView, admin_dashboard, LogoutView, staff_dashboard
# from rest_framework_simplejwt.views import TokenRefreshView

# urlpatterns = [
#     path('register/', RegisterView.as_view(), name='register'),
#     path('login/', MyTokenObtainPairView.as_view(), name='login'),
#     path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
#     path('admin-dashboard/', admin_dashboard, name='admin-dashboard'),
#     path('staff-dashboard/', staff_dashboard, name='staff-dashboard'),
#     path("logout/", LogoutView.as_view(), name="logout"),
# ]



from django.urls import path
from .views import RegisterView, MyTokenObtainPairView, admin_dashboard, staff_dashboard, LogoutView
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', MyTokenObtainPairView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('admin-dashboard/', admin_dashboard, name='admin-dashboard'),
    path('staff-dashboard/', staff_dashboard, name='staff-dashboard'),
]
