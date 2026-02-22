

from django.db import models
from centers.models import Center
from django.contrib.auth import get_user_model

User = get_user_model()

class Notice(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    center = models.ForeignKey(
        Center,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="If null, notice is for all centers"
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title
