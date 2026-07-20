

from rest_framework import serializers
from .models import Center, CenterMobile, Lifafa, LifafaPaper, CenterEmail
from django.db.models import Count
from students.models import Student
from datetime import datetime
from django.db.models import Count
from rest_framework import serializers
from centers.models import Center

from students.models import Student
from academics.models import ExamTimeTable




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


def paper_order(value):

    if not value:
        return 999

    value = str(value).upper()

    if "FIRST" in value:
        return 1

    if "SECOND" in value:
        return 2

    if "THIRD" in value:
        return 3

    if "FOURTH" in value:
        return 4

    return 999



def normalize_class_name(value):

    if not value:
        return ""

    value = str(value).upper().strip()


    replacements = {

        # IBTIDAI
        "IBTIDAI_SAAL_AWWAL": "IBTIDAIA-AWWAL",
        "IBTIDAI SAAL AWWAL": "IBTIDAIA-AWWAL",
        "IBTIDAI_SAAL_DOAM": "IBTIDAIA-DOAM",
        "IBTIDAI SAAL DOAM": "IBTIDAIA-DOAM",

        "IBTIDAIA-AWWAL": "IBTIDAIA-AWWAL",
        "IBTIDAIA-DOAM": "IBTIDAIA-DOAM",


        # SANVIYA
        "SANVIYA_SAAL_AWWAL": "SANVIYA-AWWAL",
        "SANVIYA SAAL AWWAL": "SANVIYA-AWWAL",
        "SANVIYA_SAAL_DOAM": "SANVIYA-DOAM",
        "SANVIYA SAAL DOAM": "SANVIYA-DOAM",

        "SANVIYA-AWWAL": "SANVIYA-AWWAL",
        "SANVIYA-DOAM": "SANVIYA-DOAM",


        # ALIYA
        "ALIYA_SAAL_AWWAL": "ALIYA-AWWAL",
        "ALIYA SAAL AWWAL": "ALIYA-AWWAL",
        "ALIYA_SAAL_DOAM": "ALIYA-DOAM",
        "ALIYA SAAL DOAM": "ALIYA-DOAM",

        "ALIYA-AWWAL": "ALIYA-AWWAL",
        "ALIYA-DOAM": "ALIYA-DOAM",

    }


    return replacements.get(
        value,
        value
    )

def get_paper_name_from_session(session):

    return {
        "1": "first paper",
        "2": "second paper",
        "3": "third paper",
        "4": "fourth paper",
    }.get(str(session))



class LifafaSerializer(serializers.ModelSerializer):

    center = serializers.SerializerMethodField()

    exam_date = serializers.SerializerMethodField()

    papers = serializers.SerializerMethodField()

    session_display = serializers.CharField(
        source="get_session_display",
        read_only=True
    )

    total_urdu = serializers.SerializerMethodField()
    total_hindi = serializers.SerializerMethodField()
    total_students = serializers.SerializerMethodField()



    class Meta:

        model = Lifafa

        fields = [
            "id",
            "center",
            "exam_date",
            "session",
            "session_display",
            "papers",
            "total_urdu",
            "total_hindi",
            "total_students",
        ]



    def get_center(self,obj):

        return {
            "id":obj.center.id,
            "center_id":obj.center.center_id,
            "center_name":obj.center.center_name
        }



    def get_timetable_map(self):

        if hasattr(self,"_timetable_map"):
            return self._timetable_map


        timetable = ExamTimeTable.objects.filter(
            center=None
        ).values(
            "paper",
            "exam_date",
            "time"
        )


        self._timetable_map={}


        for item in timetable:

            key = item["paper"].lower().strip()

            self._timetable_map[key]={
                "date":item["exam_date"],
                "time":item["time"]
            }


        return self._timetable_map



    def get_exam_date(self,obj):

        paper_name = get_paper_name_from_session(
            obj.session
        )

        if not paper_name:
            return None


        timetable = self.get_timetable_map().get(
            paper_name
        )

        if timetable:
            return timetable["date"]

        return None

    def get_student_stats(self,obj):

        cache_key=f"stats_{obj.id}"


        if hasattr(self,cache_key):
            return getattr(self,cache_key)

        year = (
            self.get_exam_date(obj).year
            if self.get_exam_date(obj)
            else None
        )

        if not year:
            return {}

        students = Student.objects.filter(
            center=obj.center,
            session=str(year)
        ).values(
            "student_class",
            "medium"
        ).annotate(
            count=Count("id")
        )

        result={}

        for row in students:

            cls=normalize_class_name(
                row["student_class"]
            )


            if cls not in result:

                result[cls]={
                    "total":0,
                    "urdu":0,
                    "hindi":0
                }


            result[cls]["total"]+=row["count"]


            medium=(row["medium"] or "").lower()


            if medium=="urdu":
                result[cls]["urdu"]+=row["count"]


            if medium=="hindi":
                result[cls]["hindi"]+=row["count"]

        setattr(
            self,
            cache_key,
            result
        )

        return result


    def get_papers(self,obj):


        stats=self.get_student_stats(obj)


        result=[]


        for paper in sorted(
            obj.papers.all(),
            key=lambda x: paper_order(x.paper_no)
        ):


            data=stats.get(
                normalize_class_name(
                    paper.exam_name
                ),
                {
                    "total":0,
                    "urdu":0,
                    "hindi":0
                }
            )


            result.append({

                "exam_name":
                    paper.exam_name,

                "paper_no":
                    paper.paper_no,

                "total":
                    data["total"],

                "urdu":
                    data["urdu"],

                "hindi":
                    data["hindi"]

            })


        return result


    def get_total_urdu(self,obj):

        return sum(
            x["urdu"]
            for x in self.get_papers(obj)
        )

    def get_total_hindi(self,obj):

        return sum(
            x["hindi"]
            for x in self.get_papers(obj)
        )

    def get_total_students(self,obj):

        return (
            self.get_total_urdu(obj)
            +
            self.get_total_hindi(obj)
        )