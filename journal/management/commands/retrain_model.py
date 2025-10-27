from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '../../../journal/ml'))
from train_model import HealthModelTrainer

class Command(BaseCommand):
    help = 'Ré-entraîne automatiquement le modèle IA chaque mois'
    
    def handle(self, *args, **options):
        self.stdout.write('🔄 Vérification de la nécessité de ré-entraînement...')
        
        # Vérifier si le modèle a plus d'un mois
        model_path = 'journal/ml/trained_health_model.joblib'
        if os.path.exists(model_path):
            model_age = timezone.now() - timezone.datetime.fromtimestamp(
                os.path.getmtime(model_path)
            )
            
            if model_age < timedelta(days=30):
                self.stdout.write('✅ Modèle récent, pas besoin de ré-entraînement')
                return
        
        # Ré-entraînement nécessaire
        self.stdout.write('🔧 Ré-entraînement du modèle...')
        trainer = HealthModelTrainer()
        mae, r2 = trainer.train_model(use_real_data=True)
        
        if trainer.save_model():
            self.stdout.write(self.style.SUCCESS(
                f'✅ Modèle ré-entraîné avec succès! MAE: {mae:.2f}, R²: {r2:.2f}'
            ))