"""
Models for the HEALTH TRACK recommendation system.

WARNING: This system provides lifestyle recommendations only.
NO medical diagnosis or prescription is performed.
"""
from django.conf import settings
from django.db import models


class Profile(models.Model):
    """Extended user profile with health-related metadata for personalization."""
    ACTIVITY_LEVEL_CHOICES = [
        ('sedentary', 'Sédentaire (peu ou pas d\'exercice)'),
        ('light', 'Légèrement actif (1-3 jours/semaine)'),
        ('moderate', 'Modérément actif (3-5 jours/semaine)'),
        ('very_active', 'Très actif (6-7 jours/semaine)'),
        ('extra_active', 'Extrêmement actif (2x par jour)'),
    ]
    
    GOAL_CHOICES = [
        ('weight_loss', 'Perte de poids'),
        ('muscle_gain', 'Prise de masse musculaire'),
        ('fitness', 'Amélioration de la forme physique'),
        ('health', 'Santé générale'),
        ('sleep', 'Amélioration du sommeil'),
        ('stress', 'Réduction du stress'),
    ]
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    
    # Basic info
    sex = models.CharField(max_length=10, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    height_cm = models.FloatField(null=True, blank=True)
    weight_kg = models.FloatField(null=True, blank=True)
    
    # Personalization fields (NEW)
    activity_level = models.CharField(
        max_length=20,
        choices=ACTIVITY_LEVEL_CHOICES,
        blank=True,
        help_text="Niveau d'activité physique habituel"
    )
    health_goals = models.CharField(
        max_length=50,
        choices=GOAL_CHOICES,
        blank=True,
        help_text="Objectif de santé principal"
    )
    medical_conditions = models.TextField(
        blank=True,
        help_text="Conditions médicales connues (optionnel, pour information uniquement)"
    )
    preferences = models.JSONField(
        default=dict,
        blank=True,
        help_text="Préférences utilisateur (notifications, types de conseils, etc.)"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile: {self.user.username}"
    
    @property
    def age(self):
        """Calculate age from birth_date."""
        if not self.birth_date:
            return None
        from datetime import date
        today = date.today()
        return today.year - self.birth_date.year - (
            (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
        )
    
    @property
    def bmi(self):
        """Calculate BMI from height and weight."""
        if not self.height_cm or not self.weight_kg:
            return None
        height_m = self.height_cm / 100
        return round(self.weight_kg / (height_m ** 2), 1)


class DailyMetrics(models.Model):
    """Daily health metrics recorded by the user."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='daily_metrics')
    date = models.DateField()
    steps = models.IntegerField(null=True, blank=True)
    sleep_hours = models.FloatField(null=True, blank=True)
    systolic_bp = models.IntegerField(null=True, blank=True)
    diastolic_bp = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.date}"

    class Meta:
        unique_together = ("user", "date")
        ordering = ['-date']


class Recommendation(models.Model):
    """
    Personalized lifestyle recommendation.
    
    WARNING: These are generic lifestyle tips, NOT medical advice.
    Always consult healthcare professionals for medical concerns.
    """
    CATEGORY_CHOICES = [
        ("activity", "activity"),
        ("nutrition", "nutrition"),
        ("sleep", "sleep"),
        ("lifestyle", "lifestyle")
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='recommendations')
    created_at = models.DateTimeField(auto_now_add=True)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES)
    text = models.TextField()
    rationale = models.TextField(blank=True)
    source = models.CharField(max_length=50, default="rule")
    score = models.FloatField(default=0.0)
    
    # User feedback fields for ML training
    viewed = models.BooleanField(default=False, help_text="User viewed this recommendation")
    viewed_at = models.DateTimeField(null=True, blank=True)
    helpful = models.BooleanField(null=True, blank=True, help_text="User feedback: was this helpful?")
    feedback_at = models.DateTimeField(null=True, blank=True)
    acted_upon = models.BooleanField(default=False, help_text="User indicated they acted on this")
    
    # Metadata for model versioning and A/B testing
    model_version = models.CharField(max_length=50, blank=True, help_text="Version of model that generated this")
    experiment_group = models.CharField(max_length=50, blank=True, help_text="A/B test group identifier")

    def __str__(self):
        return f"{self.user.username} - {self.category} - {self.created_at.date()}"

    class Meta:
        ordering = ['-score', '-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['source', 'created_at']),
            models.Index(fields=['helpful']),
        ]
