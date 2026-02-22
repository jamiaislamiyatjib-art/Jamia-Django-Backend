
from django.contrib import admin
from .models import Student

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = (
        "student_name",
        "roll_no",
        "student_class",
        "session",
        "result",
        "division",
        "is_published",
        "is_admit_card_published",
    )

    list_filter = (
        "student_class",
        "session",
        "is_published",
        "is_admit_card_published",
        "result",
    )

    search_fields = (
        "student_name",
        "roll_no",
        "enroll_no",
    )

    actions = [
        "publish_results",
        "unpublish_results",
        "publish_admit_cards",
        "unpublish_admit_cards",
    ]

    # 🔹 RESULT PUBLISH
    def publish_results(self, request, queryset):
        queryset.update(is_published=True)

    def unpublish_results(self, request, queryset):
        queryset.update(is_published=False)

    publish_results.short_description = "Publish selected results"
    unpublish_results.short_description = "Unpublish selected results"

    # 🔹 ADMIT CARD PUBLISH
    def publish_admit_cards(self, request, queryset):
        queryset.update(is_admit_card_published=True)

    def unpublish_admit_cards(self, request, queryset):
        queryset.update(is_admit_card_published=False)

    publish_admit_cards.short_description = "Publish Admit Cards"
    unpublish_admit_cards.short_description = "Unpublish Admit Cards"

