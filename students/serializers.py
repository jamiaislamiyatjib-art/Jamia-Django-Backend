
from rest_framework import serializers
from .models import Student
from rest_framework.pagination import PageNumberPagination
from num2words import num2words
from django.db import transaction
from .models import Center



# class StudentSerializer(serializers.ModelSerializer):
#     paper1 = serializers.IntegerField(allow_null=True, required=False)
#     paper2 = serializers.IntegerField(allow_null=True, required=False)
#     paper3 = serializers.IntegerField(allow_null=True, required=False)
#     paper4 = serializers.IntegerField(allow_null=True, required=False)
    
#     admission_type = serializers.CharField(read_only=True)
    
#     center_id = serializers.CharField(
#         source="center.center_id",
#         read_only=True
#     )

#     center_name = serializers.CharField(
#         source="center.center.name",
#         read_only=True
#     )

#     class Meta:
#         model = Student
#         fields = '__all__'
#         read_only_fields = (
#             "total",
#             "avg_percentage",
#             "result",
#             "division",
#             "grand_total",
#         )


class StudentSerializer(serializers.ModelSerializer):
    paper1 = serializers.IntegerField(allow_null=True, required=False)
    paper2 = serializers.IntegerField(allow_null=True, required=False)
    paper3 = serializers.IntegerField(allow_null=True, required=False)
    paper4 = serializers.IntegerField(allow_null=True, required=False)
    
    admission_type = serializers.CharField(read_only=True)

    # For writes
    center = serializers.PrimaryKeyRelatedField(
        queryset=Center.objects.all(), 
        required=False, 
        allow_null=True
    )

    # For reads only
    center_id = serializers.CharField(source="center.center_id", read_only=True)
    center_name = serializers.CharField(source="center.name", read_only=True)

    class Meta:
        model = Student
        fields = '__all__'
        read_only_fields = (
            "total",
            "avg_percentage",
            "result",
            "division",
            "grand_total",
        )


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'limit'
    max_page_size = 100
    

class StudentResultSerializer(serializers.ModelSerializer):
    center_name = serializers.CharField(source="center.center_name", read_only=True)

    class Meta:
        model = Student
        fields = [
            "student_name",
            "roll_no",
            "father_husband_name",
            "student_class",
            "session",
            "medium",
            "paper1",
            "paper2",
            "paper3",
            "paper4",
            "total",
            "avg_percentage",
            "result",
            "division",
            "city",
            "center_name",
            "is_published",
        ]

class AdmitCardSerializer(serializers.ModelSerializer):
    center_name = serializers.CharField(source="center.center_name", read_only=True)
    center_code = serializers.CharField(source="center.center_id", read_only=True)

    class Meta:
        model = Student
        fields = [
            "student_name",
            "father_husband_name",
            "roll_no",
            "enroll_no",
            "student_class",
            "session",
            "medium",
            "gender",
            "city",
            "place",
            "center_name",
            "center_code",
        ]
        

class SummarySerializer(serializers.Serializer):
    total = serializers.IntegerField()
    present = serializers.IntegerField()
    absent = serializers.IntegerField()
    pass_count = serializers.IntegerField()
    fail_count = serializers.IntegerField()
    first_division = serializers.IntegerField()
    second_division = serializers.IntegerField()
    third_division = serializers.IntegerField()


class LifafaSerializer(serializers.ModelSerializer):
    center_name = serializers.CharField(source="center.center_name")

    class Meta:
        model = Student
        fields = [
            "student_name", "father_husband_name",
            "roll_no", "student_class",
            "city", "place", "center_name"
        ]
        
        


class MarksheetSerializer(serializers.ModelSerializer):
    center_name = serializers.CharField(source="center.center_name", read_only=True)
    max_total = serializers.SerializerMethodField()
    total_words = serializers.SerializerMethodField()

    class Meta:
        model = Student
        fields = [
            "student_name",
            "father_husband_name",
            "roll_no",
            "enroll_no",
            "student_class",
            "session",
            "place",
            "medium",
            "paper1",
            "paper2",
            "paper3",
            "paper4",
            "total",
            "avg_percentage",
            "result",
            "division",
            "center_name",
            "max_total",
            "total_words",
        ]

    def get_total_words(self, obj):
        return num2words(obj.total).title() if obj.total else "Zero"

    def get_max_total(self, obj):
        return obj.grand_total
    

class MeritListSerializer(serializers.Serializer):
    roll_no = serializers.CharField()
    enroll_no = serializers.CharField()
    center_id = serializers.CharField()
    student_name = serializers.CharField()
    previous = serializers.IntegerField()
    current = serializers.IntegerField()
    two_year_total = serializers.IntegerField()
    rank = serializers.IntegerField()



class ReportRowSerializer(serializers.ModelSerializer):
    center_name = serializers.CharField(source="center.center_name", read_only=True)
    center_id = serializers.CharField(source="center.center_id", read_only=True)

    class Meta:
        model = Student
        fields = [
            "student_id",
            "roll_no",
            "enroll_no",
            "student_name",
            "father_husband_name",
            "gender",
            "student_class",
            "session",
            "medium",
            "city",
            "center_id",
            "center_name",
            "result",
            "division",
            "avg_percentage",
        ]
