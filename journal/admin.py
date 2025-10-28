from django.contrib import admin
from .models import MoodEntry

@admin.register(MoodEntry)
class MoodEntryAdmin(admin.ModelAdmin):
    list_display = ("user", "emotion", "intensity", "created_at")
    list_filter = ("emotion", "created_at")
    search_fields = ("user__username", "text")
# Register your models here.
