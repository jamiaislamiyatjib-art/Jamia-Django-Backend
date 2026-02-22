

from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from .serializers import UserSerializer, MyTokenObtainPairSerializer
from .models import User

# Login
class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

# Register
class RegisterView(generics.CreateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]

# Logout
class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response({"error": "Refresh token is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"message": "Logged out successfully"}, status=status.HTTP_205_RESET_CONTENT)
        except TokenError:
            return Response({"error": "Invalid or expired token"}, status=status.HTTP_400_BAD_REQUEST)

# Admin Dashboard
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def admin_dashboard(request):
    if request.user.role != 'admin':
        return Response({'error': 'Forbidden'}, status=403)
    return Response({'message': 'Welcome Admin!'})

# Staff Dashboard (center-based)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def staff_dashboard(request):
    if request.user.role != 'staff' or not request.user.center:
        return Response({'error': 'Forbidden'}, status=403)
    return Response({
        'message': f'Welcome Staff of {request.user.center.center_name}',
        'center_id': request.user.center.id,
        'center_name': request.user.center.center_name
    })
