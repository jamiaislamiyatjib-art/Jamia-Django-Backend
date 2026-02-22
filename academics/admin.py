from django.contrib import admin
from .models import Course, Fee, ExamTimeTable
# Register your models here.
admin.site.register(Course)
admin.site.register(Fee)
admin.site.register(ExamTimeTable)