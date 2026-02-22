from rest_framework import serializers
from .models import Course, Fee , ExamTimeTable

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
    center_name = serializers.CharField(
        source="center.name", read_only=True
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
