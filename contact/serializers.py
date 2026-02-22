from rest_framework import serializers
from .models import ContactMessage

class ContactMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = ["id", "full_name", "email", "message", "created_at"]

    def validate_full_name(self, value):
        if len(value) < 3:
            raise serializers.ValidationError("Name must be at least 3 characters")
        return value
