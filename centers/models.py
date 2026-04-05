

from django.db import models


class Center(models.Model):
    serial_no = models.PositiveIntegerField(unique=True)

    center_id = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique Center ID"
    )

    center_name = models.CharField(
        max_length=200,
        help_text="Center Name"
    )

    address = models.TextField()

    state = models.CharField(max_length=100)
    city = models.CharField(max_length=100)

    pincode = models.CharField(max_length=10)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['id']
        verbose_name = "Center"
        verbose_name_plural = "Centers"

    def __str__(self):
        return f"{self.center_name} ({self.center_id})"


class CenterMobile(models.Model):
    center = models.ForeignKey(
        Center,
        on_delete=models.CASCADE,
        related_name="mobile_numbers"
    )
    mobile = models.CharField(
        max_length=15,
        help_text="Contact mobile number"
    )
    is_primary = models.BooleanField(default=False)

    def __str__(self):
        return self.mobile


class CenterEmail(models.Model):
    center = models.ForeignKey(
        Center,
        on_delete=models.CASCADE,
        related_name="emails"
    )
    email = models.CharField(
        max_length=100,
        help_text="email id"
    )
    is_primary = models.BooleanField(default=False)

    def __str__(self):
        return self.email


class Lifafa(models.Model):
    SESSION_CHOICES = (
        ("1", "First Morning"),
        ("2", "Second Evening"),
        ("3", "Third Morning"),
        ("4", "Fourth Evening"),
    )

    center = models.ForeignKey(
        "Center",
        on_delete=models.CASCADE,
        related_name="lifafas"
    )

    exam_date = models.DateField()
    session = models.CharField(max_length=10, choices=SESSION_CHOICES)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.center} - {self.session}"


class LifafaPaper(models.Model):
    lifafa = models.ForeignKey(
        Lifafa,
        on_delete=models.CASCADE,
        related_name="papers"
    )

    exam_name = models.CharField(max_length=200)
    paper_no = models.PositiveIntegerField()

    def __str__(self):
        return self.exam_name