from django.db import models
from django.conf import settings
from textblob import TextBlob  # pour analyse de sentiment simple
from django.utils import timezone
import datetime

class MoodEntry(models.Model):
    EMOTIONS = [
        ("joyeux", "Joyeux"),
        ("calme", "Calme"),
        ("stresse", "Stressé"),
        ("triste", "Triste"),
        ("fatigue", "Fatigué"),
        ("colere", "En colère"),
        ("anxieux", "Anxieux"),
        ("neutre", "Neutre"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="mood_entries"
    )
    text = models.TextField(verbose_name="Description du ressenti", blank=True)
    emotion = models.CharField(max_length=30, choices=EMOTIONS, blank=True, null=True)
    intensity = models.PositiveSmallIntegerField(null=True, blank=True, help_text="1 à 10")
    mood_score = models.FloatField(null=True, blank=True, help_text="Score calculé automatiquement")
    sentiment_score = models.FloatField(null=True, blank=True, help_text="Analyse sentiment du texte")
    tags = models.CharField(max_length=200, blank=True)
    objectives = models.TextField(blank=True, help_text="Objectifs suggérés par l'IA")
    recommendations = models.TextField(blank=True, help_text="Recommandations pour améliorer l'humeur")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} — {self.emotion or 'Non analysé'} — {self.created_at:%Y-%m-%d %H:%M}"

    def save(self, *args, **kwargs):
        # 1️⃣ Analyse de sentiment du texte
        if self.text:
            blob = TextBlob(self.text)
            self.sentiment_score = blob.sentiment.polarity  # -1 à +1
        else:
            self.sentiment_score = 0

        # 2️⃣ Calcul automatique du mood_score
        self.mood_score = self.intensity or 0
        if self.emotion in ["triste", "stresse", "colere", "anxieux", "fatigue"]:
            self.mood_score *= -1
        elif self.emotion in ["joyeux", "calme"]:
            self.mood_score *= 1.2

        # Combinaison avec sentiment du texte
        self.mood_score += self.sentiment_score * 5

        # 3️⃣ Génération automatique de tags avancés
        if self.text:
            text_lower = self.text.lower()
            keywords = {
                "stress": "stress",
                "fatigue": "fatigue",
                "heureux": "joie",
                "calme": "calme",
                "angoisse": "anxiété",
                "colère": "colère",
                "triste": "tristesse",
                "déprimé": "tristesse",
                "content": "joie"
            }
            self.tags = " ".join([tag for kw, tag in keywords.items() if kw in text_lower])

        # 4️⃣ Génération automatique d'objectifs et recommandations
        objectives, recommendations = [], []

        if self.mood_score < 0:
            recommendations.append("Prends une pause, respire profondément ou médite 10 minutes")
            recommendations.append("Écris tes émotions pour te soulager")
            objectives.append("Réduire le stress quotidien")
        elif self.mood_score <= 3:
            recommendations.append("Fais une activité qui te fait plaisir")
            objectives.append("Améliorer l'humeur progressivement")
        else:
            recommendations.append("Continue tes bonnes habitudes !")
            objectives.append("Maintenir cet état positif")

        if "fatigue" in self.tags:
            recommendations.append("Dors au moins 7 heures cette nuit")
            objectives.append("Gérer la fatigue")
        if "stress" in self.tags or "anxiété" in self.tags:
            recommendations.append("Essaie une session de relaxation ou yoga")
            objectives.append("Réduire le stress")

        self.objectives = " • ".join(objectives)
        self.recommendations = " • ".join(recommendations)

        super().save(*args, **kwargs)

    # 5️⃣ Méthodes utilitaires
    @staticmethod
    def average_score(user, days=7):
        """Moyenne du score sur les derniers jours"""
        start_date = timezone.now() - datetime.timedelta(days=days)
        entries = MoodEntry.objects.filter(user=user, created_at__gte=start_date)
        if entries.exists():
            return round(sum(e.mood_score for e in entries)/entries.count(), 2)
        return 0

    @staticmethod
    def last_entries(user, count=5):
        """Retourne les derniers 'count' entrées d'un utilisateur"""
        return MoodEntry.objects.filter(user=user).order_by('-created_at')[:count]
