

from rest_framework import serializers
from .models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from centers.models import Center

# Registration Serializer
class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'role', 'center']

    def validate(self, data):
        if data['role'] == 'staff' and not data.get('center'):
            raise serializers.ValidationError({"center": "Staff must be assigned to a center"})
        return data

    def create(self, validated_data):
        user = User.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
            role=validated_data['role'],
            center=validated_data.get('center')
        )
        user.set_password(validated_data['password'])
        user.save()
        return user

# Custom JWT to include role and center
class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data['role'] = self.user.role
        data['username'] = self.user.username
        data['email'] = self.user.email
        data['center_id'] = self.user.center.id if self.user.center else None
        data['center_name'] = self.user.center.center_name if self.user.center else None
        return data

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["username"] = user.username
        token["role"] = user.role
        token["center_id"] = user.center.id if user.center else None
        return token
