from django.db import models
from django.conf import settings  # <-- important

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
        settings.AUTH_USER_MODEL,   # <-- au lieu de auth.User
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
