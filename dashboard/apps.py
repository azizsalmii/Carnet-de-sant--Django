# dashboard/apps.py
import os
from django.apps import AppConfig
from django.conf import settings

class DashboardConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "dashboard"

    def ready(self):
        """
        Crée un superuser par défaut en DEV si aucun n'existe.
        Utilise les variables d'env si fournies, sinon des valeurs par défaut.
        """
        if not settings.DEBUG:
            return

        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            if not User.objects.filter(is_superuser=True).exists():
                username = os.getenv("BOOTSTRAP_ADMIN_USERNAME", "admin")
                email = os.getenv("BOOTSTRAP_ADMIN_EMAIL", "admin@example.com")
                password = os.getenv("BOOTSTRAP_ADMIN_PASSWORD", "admin123")
                u = User.objects.create_superuser(username=username, email=email, password=password)
                print(f"[dashboard] Superuser auto-créé: {username} / {password}")
        except Exception as e:
            print("[dashboard] Création superuser: ignorée (", e, ")")
