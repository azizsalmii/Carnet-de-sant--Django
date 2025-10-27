# ai_models/admin.py
from django.contrib import admin
from .models import Diagnosis

@admin.register(Diagnosis)
class DiagnosisAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "modality", "predicted_class", "confidence", "created_at")
    list_filter = ("modality", "created_at")
    search_fields = ("user__username", "predicted_class")
