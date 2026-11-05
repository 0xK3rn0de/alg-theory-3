from django.contrib import admin

from .models import GenerationActivity, MemeTemplate


@admin.register(MemeTemplate)
class MemeTemplateAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "created_at")
    search_fields = ("title", "category", "top_text", "bottom_text")
    list_filter = ("category", "created_at")


@admin.register(GenerationActivity)
class GenerationActivityAdmin(admin.ModelAdmin):
    list_display = ("activity_date", "generation_count")
    date_hierarchy = "activity_date"