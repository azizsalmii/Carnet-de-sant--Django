from django.apps import AppConfig


class RecoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'reco'
    
    def ready(self):
        """
        Import signals when Django starts.
        This ensures the signal handlers are registered and will fire
        when users are created.
        """
        import reco.signals  # noqa: F401
