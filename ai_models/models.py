from django.db import models
from django.conf import settings


class MLModel(models.Model):
    name = models.CharField(max_length=100)
    framework = models.CharField(max_length=50, default='pytorch')
    file_path = models.FilePathField(path='', max_length=512)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Diagnosis(models.Model):
    class Modality(models.TextChoices):
        BRAIN = "brain", "Brain Tumor MRI"
        CXR   = "cxr",   "Chest X-Ray"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="diagnoses")
    modality = models.CharField(max_length=10, choices=Modality.choices)
    predicted_class = models.CharField(max_length=100)
    confidence = models.FloatField(null=True, blank=True)  # probabilité de la classe principale
    probabilities = models.JSONField(default=dict, blank=True)  # map classe → proba
    latency_ms = models.FloatField(null=True, blank=True)

    # image originale uploadée (on stocke le chemin relatif dans /media/)
    image = models.ImageField(upload_to="diagnostics/%Y/%m/%d/", blank=True, null=True)

    # Résumé texte pour affichage (ex : description + disclaimer)
    summary = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_modality_display()} — {self.predicted_class} — {self.user}"