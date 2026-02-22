


from rest_framework import serializers
from .models import Notice

class NoticeSerializer(serializers.ModelSerializer):
    # Fix center name field to match your model
    center_name = serializers.CharField(source="center.center_name", read_only=True)
    created_by_name = serializers.CharField(source="created_by.username", read_only=True)

    class Meta:
        model = Notice
        fields = [
            'id',
            'title',
            'content',
            'center',
            'center_name',
            'created_by',
            'created_by_name',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']
