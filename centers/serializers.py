

from rest_framework import serializers
from .models import Center, CenterMobile, Lifafa, LifafaPaper, CenterEmail
from django.db.models import Count
from students.models import Student
from datetime import datetime
from django.db.models import Count
from rest_framework import serializers
from centers.models import Center
# from centers.serializers import CenterSerializer


class CenterMobileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CenterMobile
        fields = ["id", "mobile", "is_primary"] 
        
class CenterEmailSerializer(serializers.ModelSerializer):
    class Meta:
        model = CenterEmail
        fields = ["id", "email", "is_primary"]

class CenterSerializer(serializers.ModelSerializer):
    mobile_numbers = CenterMobileSerializer(many=True, required=False)
    emails = CenterEmailSerializer(many=True, required=False)

    class Meta:
        model = Center
        fields = [
            "id",
            "serial_no",
            "center_id",
            "center_name",
            "address",
            "state",
            "city",
            "pincode",
            "created_at",
            "mobile_numbers",
            "emails",
        ]
        read_only_fields = ["id", "serial_no", "created_at"]

    def create(self, validated_data):
        mobiles_data = validated_data.pop("mobile_numbers", [])
        emails_data = validated_data.pop("emails", [])

        last_center = Center.objects.order_by("-serial_no").first()
        validated_data["serial_no"] = (
            last_center.serial_no + 1
        ) if last_center else 1

        center = Center.objects.create(**validated_data)

        for m in mobiles_data:
            CenterMobile.objects.create(center=center, **m)

        for e in emails_data:
            CenterEmail.objects.create(center=center, **e)

        return center

    def update(self, instance, validated_data):
        mobiles_data = validated_data.pop("mobile_numbers", [])
        emails_data = validated_data.pop("emails", [])

        # Update center fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Replace mobiles
        instance.mobile_numbers.all().delete()
        for m in mobiles_data:
            CenterMobile.objects.create(center=instance, **m)

        # Replace emails
        instance.emails.all().delete()
        for e in emails_data:
            CenterEmail.objects.create(center=instance, **e)

        return instance



class LifafaPaperSerializer(serializers.ModelSerializer):
    class Meta:
        model = LifafaPaper
        fields = "__all__"



# ----------------------------------------
# 🔥 CLASS NAME NORMALIZER
# ----------------------------------------
def normalize_class_name(name):
    """
    Convert:
    IBTIDAIA-AWWAL -> IBTIDAI SAAL AWWAL
    SANVIYA-AWWAL  -> SANVIYA SAAL AWWAL
    ALIYA-DOAM     -> ALIYA SAAL DOAM
    """

    if not name:
        return ""

    name = name.upper().strip()
    parts = name.split("-")

    if len(parts) == 2:
        main = parts[0]
        year = parts[1]

        # Fix spelling mismatch
        if main == "IBTIDAIA":
            main = "IBTIDAI"

        return f"{main} SAAL {year}"

    return name


# ----------------------------------------
# 🔥 LIFAFA SERIALIZER
# ----------------------------------------
class LifafaSerializer(serializers.ModelSerializer):
    center = CenterSerializer(read_only=True)
    papers = serializers.SerializerMethodField()
    session_display = serializers.CharField(
        source="get_session_display",
        read_only=True
    )

    class Meta:
        model = Lifafa
        fields = "__all__"

    def get_papers(self, obj):

        print("\n========== LIFAFA DEBUG START ==========")

        exam_year = obj.exam_date.year if obj.exam_date else None
        print("Exam Year:", exam_year)

        if not exam_year:
            print("❌ No exam year found")
            return []

        # 🔥 SAFE FK FILTER
        students = Student.objects.filter(
            center=obj.center,
            session=str(exam_year),
            # exam_session=obj.session
            # is_published=True
        )

        print("Filtered Students Count:", students.count())

        # ----------------------------------------
        # 🔥 AGGREGATE BY CLASS + MEDIUM
        # ----------------------------------------
        stats = (
            students
            .values("student_class", "medium")
            .annotate(count=Count("id"))
        )

        stats_dict = {}

        for row in stats:
            class_name = (row["student_class"] or "").upper().strip()
            medium = (row["medium"] or "").lower().strip()
            count = row["count"]

            if class_name not in stats_dict:
                stats_dict[class_name] = {
                    "total": 0,
                    "urdu": 0,
                    "hindi": 0
                }

            stats_dict[class_name]["total"] += count

            if medium == "urdu":
                stats_dict[class_name]["urdu"] += count
            elif medium == "hindi":
                stats_dict[class_name]["hindi"] += count

        print("Final Stats Dict:", stats_dict)

        # ----------------------------------------
        # 🔥 ATTACH STATS TO PAPERS
        # ----------------------------------------
        result = []

        for paper in obj.papers.all():

            print("Checking Paper:", paper.exam_name)

            normalized_name = normalize_class_name(paper.exam_name)
            print("Normalized Name:", normalized_name)

            stat = stats_dict.get(normalized_name)

            if not stat:
                print("❌ No match found")
                stat = {"total": 0, "urdu": 0, "hindi": 0}
            else:
                print("✅ Match found:", stat)

            result.append({
                "exam_name": paper.exam_name,
                "paper_no": paper.paper_no,
                "total": stat["total"],
                "urdu": stat["urdu"],
                "hindi": stat["hindi"],
            })

        print("========== LIFAFA DEBUG END ==========\n")

        return result