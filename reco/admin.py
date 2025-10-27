"""
Django admin configuration for HEALTH TRACK models.
"""
from django.contrib import admin
from .models import Profile, DailyMetrics, Recommendation


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """Admin interface for user profiles."""
    list_display = ['user', 'sex', 'birth_date', 'height_cm', 'weight_kg']
    list_filter = ['sex']
    search_fields = ['user__username', 'user__email']
    raw_id_fields = ['user']


@admin.register(DailyMetrics)
class DailyMetricsAdmin(admin.ModelAdmin):
    """Admin interface for daily metrics."""
    list_display = ['user', 'date', 'steps', 'sleep_hours', 'systolic_bp', 'diastolic_bp']
    list_filter = ['date']
    search_fields = ['user__username']
    date_hierarchy = 'date'
    raw_id_fields = ['user']
    ordering = ['-date']


@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    """Admin interface for recommendations."""
    list_display = ['user', 'category', 'score', 'source', 'created_at', 'short_text']
    list_filter = ['category', 'source', 'created_at']
    search_fields = ['user__username', 'text']
    date_hierarchy = 'created_at'
    raw_id_fields = ['user']
    ordering = ['-score', '-created_at']
    
    def short_text(self, obj):
        """Display truncated recommendation text."""
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    short_text.short_description = 'Recommendation'
