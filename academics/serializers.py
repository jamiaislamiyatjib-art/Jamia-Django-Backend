from rest_framework import serializers
from .models import Course, Fee , ExamTimeTable
from rest_framework import viewsets, status, filters
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from django.db.models import Q
from centers.models import Center

class FeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fee
        fields = '__all__'

class CourseSerializer(serializers.ModelSerializer):
    fee = FeeSerializer(read_only=True)

    class Meta:
        model = Course
        fields = '__all__'


class ExamTimeTableSerializer(serializers.ModelSerializer):
    # Return center name for display
    center_name = serializers.SerializerMethodField()
    
    # Accept PK for input, allow null for GLOBAL
    center = serializers.PrimaryKeyRelatedField(
        queryset=Center.objects.all(),
        allow_null=True,
        required=False
    )

    class Meta:
        model = ExamTimeTable
        fields = [
            "id",
            "center",
            "center_name",
            "exam_date",
            "time",
            "classes",
            "paper",
            "created_at",
        ]
        read_only_fields = ["created_at"]

    def get_center_name(self, obj):
        return obj.center.center_name if obj.center else "GLOBAL"

    # Optional: debug update
    def update(self, instance, validated_data):
        print("DEBUG update validated_data:", validated_data)
        return super().update(instance, validated_data)