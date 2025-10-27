from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

# Ancien modèle générique - nous le laissons pour la compatibilité
class JournalEntry(models.Model):
    CATEGORY_CHOICES = [
        ("symptome", "Symptôme"),
        ("traitement", "Traitement"),
        ("activite", "Activité"),
        ("sommeil", "Sommeil"),
        ("alimentation", "Alimentation"),
        ("vitaux", "Vitaux"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="journal_entries"
    )
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    content = models.TextField()
    intensity = models.IntegerField(null=True, blank=True)  # 1 à 10
    duration = models.DurationField(null=True, blank=True)  # ex: 1h30
    location = models.CharField(max_length=100, null=True, blank=True)  # ex: "tête", "dos"
    tags = models.CharField(max_length=200, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.category} - {self.user.username} - {self.created_at.date()}"

# --- Nouveaux modèles structurés pour le rapport santé ---

class HealthData(models.Model):
    """Modèle unifié pour les données de santé"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="health_data")
    date = models.DateField()
    
    # Symptômes
    symptoms = models.TextField(blank=True, null=True)
    pain_level = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        null=True, blank=True
    )
    
    # Sommeil
    sleep_duration = models.FloatField(help_text="Durée en heures", null=True, blank=True)
    sleep_quality = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="1 (mauvais) à 5 (excellent)",
        null=True, blank=True
    )
    
    # Activité physique
    steps_count = models.IntegerField(default=0)
    exercise_duration = models.FloatField(default=0, help_text="Durée en minutes")
    activity_type = models.CharField(max_length=100, blank=True)
    
    # Traitements
    medications = models.TextField(blank=True, null=True)
    medication_adherence = models.BooleanField(default=True)
    
    # Données médicales
    blood_pressure_systolic = models.IntegerField(null=True, blank=True)
    blood_pressure_diastolic = models.IntegerField(null=True, blank=True)
    heart_rate = models.IntegerField(null=True, blank=True)
    weight = models.FloatField(null=True, blank=True, help_text="Poids en kg")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date']
        verbose_name = "Donnée Santé"
        verbose_name_plural = "Données Santé"

    def __str__(self):
        return f"{self.user.username} - {self.date}"

class MonthlyReport(models.Model):
    """Rapport santé mensuel généré automatiquement"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="monthly_reports")
    month = models.DateField(help_text="Premier jour du mois")
    report_content = models.JSONField()
    generated_at = models.DateTimeField(auto_now_add=True)
    is_finalized = models.BooleanField(default=False)
    
    # Scores générés par l'IA
    health_score = models.FloatField(null=True, blank=True)
    risk_factors = models.JSONField(default=list)
    recommendations = models.JSONField(default=list)
    
    class Meta:
        unique_together = ['user', 'month']
        ordering = ['-month']
        verbose_name = "Rapport Mensuel"
        verbose_name_plural = "Rapports Mensuels"

    def __str__(self):
        return f"Rapport {self.month.strftime('%B %Y')} - {self.user.username}"

class MedicalImage(models.Model):
    """Stockage des images médicales avec analyse IA"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="medical_images")
    title = models.CharField(max_length=100)
    image = models.ImageField(upload_to='medical_images/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    analysis_result = models.TextField(blank=True)
    confidence_score = models.FloatField(null=True, blank=True, help_text="Score de confiance de l'analyse IA")

    def __str__(self):
        return f"Image: {self.title} ({self.user.username})"