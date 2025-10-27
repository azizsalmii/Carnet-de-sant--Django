from django.db import models

class HealthData(models.Model):
    user_id = models.IntegerField(unique=True)
    age = models.IntegerField()
    gender = models.CharField(max_length=10)
    sleep_duration = models.FloatField()
    sleep_quality = models.IntegerField()
    steps_daily = models.IntegerField()
    heart_rate_resting = models.IntegerField()
    blood_pressure_systolic = models.IntegerField()
    stress_level = models.IntegerField()
    bmi = models.FloatField()
    health_score = models.FloatField()
    health_category = models.CharField(max_length=20)
    is_anomaly = models.BooleanField(default=False)
    predicted_anomaly = models.BooleanField(default=False)
    anomaly_confidence = models.FloatField(default=0.0)
    risk_level = models.CharField(max_length=10, default='Low')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'health_data'
        verbose_name = 'Donnée de Santé'
        verbose_name_plural = 'Données de Santé'

class HealthAlert(models.Model):
    SEVERITY_CHOICES = [
        ('critical', 'Critique'),
        ('high', 'Élevé'),
        ('medium', 'Moyen'),
        ('positive', 'Positif'),
    ]
    
    CATEGORY_CHOICES = [
        ('sleep', 'Sommeil'),
        ('cardiac', 'Cardiaque'),
        ('activity', 'Activité'),
        ('lifestyle', 'Mode de vie'),
        ('overall', 'Global'),
    ]
    
    user = models.ForeignKey(HealthData, on_delete=models.CASCADE, related_name='alerts')
    alert_type = models.CharField(max_length=100)
    message = models.TextField()
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES)
    category = models.CharField(max_length=15, choices=CATEGORY_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'health_alerts'
        verbose_name = 'Alerte Santé'
        verbose_name_plural = 'Alertes Santé'
    
    def __str__(self):
        return f"Alerte {self.severity} - User {self.user.user_id}"