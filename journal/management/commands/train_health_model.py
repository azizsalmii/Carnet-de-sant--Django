from django.core.management.base import BaseCommand
import sys
import os

# Ajouter le chemin pour importer le trainer
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../journal/ml'))

from train_model import HealthModelTrainer

class Command(BaseCommand):
    help = 'Entraîne le modèle IA du carnet de santé'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--synthetic-only',
            action='store_true',
            help='Utiliser seulement des données synthétiques'
        )
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS(
            '🤖 Démarrage de l\'entraînement du modèle IA...'
        ))
        
        trainer = HealthModelTrainer()
        
        # Entraîner le modèle
        use_real_data = not options['synthetic_only']
        mae, r2 = trainer.train_model(use_real_data=use_real_data)
        
        # Sauvegarder le modèle
        if trainer.save_model():
            self.stdout.write(self.style.SUCCESS(
                f'✅ Modèle entraîné avec succès! MAE: {mae:.2f}, R²: {r2:.2f}'
            ))
        else:
            self.stdout.write(self.style.ERROR(
                '❌ Échec de l\'entraînement du modèle'
            ))