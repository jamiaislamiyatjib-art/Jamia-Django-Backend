
from django.contrib import admin
from .models import Center, CenterMobile, Lifafa, LifafaPaper, CenterEmail


class CenterMobileInline(admin.TabularInline):
    model = CenterMobile
    extra = 1

class CenterEmailInline(admin.TabularInline):
    model = CenterEmail
    extra = 1

@admin.register(Center)
class CenterAdmin(admin.ModelAdmin):
    list_display = ("center_id", "center_name", "city", "state")
    search_fields = ("center_id", "center_name")
    inlines = [CenterMobileInline, CenterEmailInline]


class LifafaPaperInline(admin.TabularInline):
    model = LifafaPaper
    extra = 1


@admin.register(Lifafa)
class LifafaAdmin(admin.ModelAdmin):
    inlines = [LifafaPaperInline]