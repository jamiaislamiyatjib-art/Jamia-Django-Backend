

from rest_framework import serializers
from .models import Notice


class NoticeSerializer(serializers.ModelSerializer):
    center_name = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Notice
        fields = [
            "id",
            "title",
            "content",
            "center",
            "center_name",
            "created_by",
            "created_by_name",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_by", "created_at", "updated_at"]

    def get_center_name(self, obj):
        return obj.center.center_name if obj.center else None

    def get_created_by_name(self, obj):
        return obj.created_by.username if obj.created_by else None