from django.contrib import admin
from django.utils.html import format_html
from .models import JournalEntry, HealthData, MonthlyReport, MedicalImage,MoodEntry

# Admin pour JournalEntry
@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
    list_display = ['user', 'category', 'content_preview', 'intensity', 'created_at',"emotion", "intensity"]
    list_filter = ['category', 'emotion''created_at', 'user']
    search_fields = ['user__username', 'content','text','tags']
    list_per_page = 20
    date_hierarchy = 'created_at'
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Contenu'

# Admin pour HealthData
@admin.register(HealthData)
class HealthDataAdmin(admin.ModelAdmin):
    list_display = ['user', 'date', 'sleep_duration', 'sleep_quality', 'steps_count', 'pain_level', 'health_score_indicator']
    list_filter = ['date', 'user', 'medication_adherence']
    search_fields = ['user__username', 'symptoms', 'medications']
    list_editable = ['sleep_duration', 'sleep_quality', 'steps_count']
    list_per_page = 20
    date_hierarchy = 'date'
    
    def health_score_indicator(self, obj):
        """Indicateur visuel du score de santé"""
        if obj.sleep_duration and obj.sleep_quality and obj.steps_count:
            score = (obj.sleep_duration / 8 * 25 + 
                    obj.sleep_quality / 5 * 25 + 
                    min(obj.steps_count / 10000 * 25, 25) +
                    (10 - (obj.pain_level or 0)) / 10 * 25)
            
            color = 'green' if score >= 70 else 'orange' if score >= 50 else 'red'
            return format_html(
                '<div style="background:{}; color:white; padding:2px 6px; border-radius:3px; text-align:center;">{:.0f}</div>',
                color, score
            )
        return '-'
    health_score_indicator.short_description = 'Score'
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('user', 'date')
        }),
        ('Symptômes', {
            'fields': ('symptoms', 'pain_level'),
            'classes': ('collapse',)
        }),
        ('Sommeil', {
            'fields': ('sleep_duration', 'sleep_quality'),
            'classes': ('collapse',)
        }),
        ('Activité physique', {
            'fields': ('steps_count', 'exercise_duration', 'activity_type'),
            'classes': ('collapse',)
        }),
        ('Traitements', {
            'fields': ('medications', 'medication_adherence'),
            'classes': ('collapse',)
        }),
        ('Signes vitaux', {
            'fields': ('blood_pressure_systolic', 'blood_pressure_diastolic', 'heart_rate', 'weight'),
            'classes': ('collapse',)
        }),
    )

# Admin pour MonthlyReport
@admin.register(MonthlyReport)
class MonthlyReportAdmin(admin.ModelAdmin):
    list_display = ['user', 'month', 'health_score_display', 'is_finalized', 'generated_at']
    list_filter = ['month', 'user', 'is_finalized', 'generated_at']
    search_fields = ['user__username']
    readonly_fields = ['generated_at']
    list_editable = ['is_finalized']
    list_per_page = 20
    date_hierarchy = 'month'
    
    def health_score_display(self, obj):
        if obj.health_score:
            color = 'green' if obj.health_score >= 70 else 'orange' if obj.health_score >= 50 else 'red'
            return format_html(
                '<div style="background:{}; color:white; padding:2px 6px; border-radius:3px; text-align:center; font-weight:bold;">{:.1f}</div>',
                color, obj.health_score
            )
        return '-'
    health_score_display.short_description = 'Score Santé'
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('user', 'month', 'is_finalized')
        }),
        ('Analyse IA', {
            'fields': ('health_score', 'risk_factors', 'recommendations'),
            'classes': ('collapse',)
        }),
        ('Contenu du rapport', {
            'fields': ('report_content',),
            'classes': ('collapse',)
        }),
        ('Métadonnées', {
            'fields': ('generated_at',),
            'classes': ('collapse',)
        }),
    )

# Admin pour MedicalImage
@admin.register(MedicalImage)
class MedicalImageAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'uploaded_at', 'confidence_score_display']
    list_filter = ['uploaded_at', 'user']
    search_fields = ['user__username', 'title', 'analysis_result']
    readonly_fields = ['uploaded_at']
    list_per_page = 20
    date_hierarchy = 'uploaded_at'
    
    def confidence_score_display(self, obj):
        if obj.confidence_score:
            color = 'green' if obj.confidence_score >= 0.8 else 'orange' if obj.confidence_score >= 0.6 else 'red'
            return format_html(
                '<div style="background:{}; color:white; padding:2px 6px; border-radius:3px; text-align:center;">{:.1%}</div>',
                color, obj.confidence_score
            )
        return '-'
    confidence_score_display.short_description = 'Confiance IA'

# Actions personnalisées
def mark_reports_finalized(modeladmin, request, queryset):
    updated = queryset.update(is_finalized=True)
    modeladmin.message_user(request, f"{updated} rapports marqués comme finalisés.")
mark_reports_finalized.short_description = "✅ Marquer les rapports comme finalisés"

def mark_reports_draft(modeladmin, request, queryset):
    updated = queryset.update(is_finalized=False)
    modeladmin.message_user(request, f"{updated} rapports marqués comme brouillon.")
mark_reports_draft.short_description = "📝 Marquer les rapports comme brouillon"

MonthlyReportAdmin.actions = [mark_reports_finalized, mark_reports_draft]
