from django.contrib import admin
from .models import HealthData, HealthAlert

@admin.register(HealthData)
class HealthDataAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'age', 'gender', 'health_score', 'health_category', 'predicted_anomaly', 'risk_level')
    list_filter = ('health_category', 'predicted_anomaly', 'risk_level', 'gender')
    search_fields = ('user_id',)
    readonly_fields = ('created_at',)

@admin.register(HealthAlert)
class HealthAlertAdmin(admin.ModelAdmin):
    list_display = ('user', 'alert_type', 'severity', 'category', 'created_at')
    list_filter = ('severity', 'category', 'created_at')
    search_fields = ('user__user_id', 'message')
    readonly_fields = ('created_at',)