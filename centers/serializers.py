

from rest_framework import serializers
from .models import Center, CenterMobile, Lifafa, LifafaPaper

class CenterMobileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CenterMobile
        fields = ["id", "mobile", "is_primary"]  # include "id" for updates if needed

class CenterSerializer(serializers.ModelSerializer):
    mobile_numbers = CenterMobileSerializer(many=True)

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
        ]
        read_only_fields = ["id", "serial_no", "created_at"]

    def create(self, validated_data):
        mobiles_data = validated_data.pop("mobile_numbers", [])
        last_center = Center.objects.order_by("-serial_no").first()
        validated_data["serial_no"] = (last_center.serial_no + 1) if last_center else 1

        center = Center.objects.create(**validated_data)

        for m in mobiles_data:
            CenterMobile.objects.create(center=center, **m)

        return center

    def update(self, instance, validated_data):
        mobiles_data = validated_data.pop("mobile_numbers", [])

        # Update center fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update mobile numbers: clear old and create new
        instance.mobile_numbers.all().delete()
        for m in mobiles_data:
            CenterMobile.objects.create(center=instance, **m)

        return instance


# class PaperSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Paper
#         fields = "__all__"


# class LifafaSerializer(serializers.ModelSerializer):

#     center = CenterSerializer()
#     papers = PaperSerializer(many=True)

#     class Meta:
#         model = Lifafa
#         fields = "__all__"

class LifafaPaperSerializer(serializers.ModelSerializer):
    class Meta:
        model = LifafaPaper
        fields = "__all__"


class LifafaSerializer(serializers.ModelSerializer):
    center = CenterSerializer()
    papers = LifafaPaperSerializer(many=True)

    class Meta:
        model = Lifafa
        fields = "__all__"