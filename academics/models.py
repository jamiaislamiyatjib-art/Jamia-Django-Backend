
from django.db import models
from centers.models import Center

class Course(models.Model):
    name = models.CharField(max_length=200)
    duration = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        return self.name


class Fee(models.Model):
    course = models.OneToOneField(Course, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default="INR")


class ExamTimeTable(models.Model):
    center = models.ForeignKey(
    Center,
    on_delete=models.SET_NULL,
    null=True,
    blank=True
)
    exam_date = models.DateField()
    time = models.CharField(max_length=50)

    # Multiple classes (one per line)
    classes = models.TextField(help_text="One class per line")

    paper = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["exam_date", "time"]
        verbose_name = "Exam Time Table"
        verbose_name_plural = "Exam Time Tables"

    def __str__(self):
        return f"{self.center} | {self.exam_date} | {self.paper}"
