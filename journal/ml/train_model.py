import os
import sys
import django
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import joblib

# Configuration Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'projetPython.settings')
django.setup()

from journal.models import HealthData, MonthlyReport
from django.contrib.auth import get_user_model

User = get_user_model()

class HealthModelTrainer:
    """Classe pour entraîner le modèle IA sur les données réelles"""
    
    def __init__(self):
        self.model = None
        self.features = [
            'sleep_duration', 'sleep_quality', 'steps_count',
            'exercise_duration', 'pain_level', 'medication_adherence'
        ]
        self.model_path = 'journal/ml/trained_health_model.joblib'
    
    def load_training_data(self):
        """Charge les données d'entraînement depuis la base"""
        print("📊 Chargement des données d'entraînement...")
        
        # Récupérer toutes les données santé
        health_data = HealthData.objects.filter(
            sleep_duration__isnull=False,
            sleep_quality__isnull=False,
            steps_count__isnull=False
        ).select_related('user')
        
        if not health_data:
            print("❌ Aucune donnée trouvée pour l'entraînement")
            return None, None
        
        features_list = []
        targets = []
        
        for data in health_data:
            # Features
            features = [
                data.sleep_duration or 7,
                data.sleep_quality or 3,
                data.steps_count or 5000,
                data.exercise_duration or 0,
                data.pain_level or 0,
                1 if data.medication_adherence else 0
            ]
            features_list.append(features)
            
            # Target: score santé calculé (vous pouvez ajuster cette formule)
            target = self._calculate_health_score_from_data(data)
            targets.append(target)
        
        print(f"✅ {len(features_list)} échantillons chargés")
        return np.array(features_list), np.array(targets)
    
    def _calculate_health_score_from_data(self, health_data):
        """Calcule un score santé à partir des données (cible pour l'entraînement)"""
        score = 100
        
        # Pénalités basées sur les recommandations médicales
        if health_data.sleep_duration:
            if health_data.sleep_duration < 6 or health_data.sleep_duration > 9:
                score -= 15
            elif health_data.sleep_duration < 7 or health_data.sleep_duration > 8:
                score -= 5
        
        if health_data.sleep_quality:
            if health_data.sleep_quality < 3:
                score -= 10
            elif health_data.sleep_quality < 4:
                score -= 5
        
        if health_data.steps_count:
            if health_data.steps_count < 5000:
                score -= 15
            elif health_data.steps_count < 7500:
                score -= 5
        
        if health_data.pain_level:
            if health_data.pain_level > 5:
                score -= (health_data.pain_level - 5) * 3
        
        if not health_data.medication_adherence:
            score -= 10
        
        return max(0, min(100, score))
    
    def generate_synthetic_data(self, n_samples=1000):
        """Génère des données synthétiques si pas assez de données réelles"""
        print("🔧 Génération de données synthétiques...")
        
        np.random.seed(42)
        
        # Données réalistes basées sur des statistiques médicales
        sleep_duration = np.random.normal(7.5, 1.2, n_samples)
        sleep_quality = np.random.normal(3.5, 0.8, n_samples)
        steps_count = np.random.normal(7500, 2500, n_samples)
        exercise_duration = np.random.normal(25, 15, n_samples)
        pain_level = np.random.normal(2.5, 1.8, n_samples)
        medication_adherence = np.random.binomial(1, 0.85, n_samples)
        
        # Features
        X = np.column_stack([
            sleep_duration, sleep_quality, steps_count,
            exercise_duration, pain_level, medication_adherence
        ])
        
        # Target: score santé calculé avec une formule réaliste
        y = (
            np.clip(sleep_duration / 9 * 25, 0, 25) +  # Sommeil: max 25
            np.clip(sleep_quality / 5 * 25, 0, 25) +   # Qualité: max 25
            np.clip(steps_count / 10000 * 25, 0, 25) + # Pas: max 25
            np.clip(exercise_duration / 60 * 15, 0, 15) + # Exercice: max 15
            np.clip((10 - pain_level) / 10 * 10, 0, 10) + # Douleur: max 10
            medication_adherence * 10  # Observance: 10 points
        )
        
        return X, y
    
    def train_model(self, use_real_data=True):
        """Entraîne le modèle IA"""
        print("🤖 Début de l'entraînement du modèle...")
        
        # Charger les données
        if use_real_data:
            X, y = self.load_training_data()
            if X is None or len(X) < 50:  # Si pas assez de données réelles
                print("📝 Pas assez de données réelles, utilisation de données synthétiques")
                X, y = self.generate_synthetic_data(1000)
        else:
            X, y = self.generate_synthetic_data(1000)
        
        # Diviser en train/test
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        print(f"📈 Données d'entraînement: {X_train.shape[0]} échantillons")
        print(f"📊 Données de test: {X_test.shape[0]} échantillons")
        
        # Entraîner le modèle
        self.model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42
        )
        
        self.model.fit(X_train, y_train)
        
        # Évaluation
        y_pred = self.model.predict(X_test)
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        print(f"✅ Modèle entraîné avec succès!")
        print(f"📊 Performance du modèle:")
        print(f"   - MAE (Erreur Absolue Moyenne): {mae:.2f}")
        print(f"   - R² (Score de détermination): {r2:.2f}")
        
        # Feature importance
        feature_importance = dict(zip(self.features, self.model.feature_importances_))
        print("🔍 Importance des features:")
        for feature, importance in sorted(feature_importance.items(), key=lambda x: x[1], reverse=True):
            print(f"   - {feature}: {importance:.3f}")
        
        return mae, r2
    
    def save_model(self):
        """Sauvegarde le modèle entraîné"""
        if self.model is None:
            print("❌ Aucun modèle à sauvegarder")
            return False
        
        # Créer le dossier si nécessaire
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        
        # Sauvegarder le modèle
        joblib.dump(self.model, self.model_path)
        print(f"💾 Modèle sauvegardé: {self.model_path}")
        return True
    
    def load_trained_model(self):
        """Charge un modèle pré-entraîné"""
        try:
            if os.path.exists(self.model_path):
                self.model = joblib.load(self.model_path)
                print(f"📂 Modèle chargé: {self.model_path}")
                return True
            else:
                print("❌ Aucun modèle pré-entraîné trouvé")
                return False
        except Exception as e:
            print(f"❌ Erreur lors du chargement du modèle: {e}")
            return False

def main():
    """Fonction principale pour l'entraînement"""
    trainer = HealthModelTrainer()
    
    print("=" * 50)
    print("🤖 ENTRAÎNEMENT DU MODÈLE IA - CARNET DE SANTÉ")
    print("=" * 50)
    
    # Essayer de charger un modèle existant d'abord
    if trainer.load_trained_model():
        print("✅ Modèle pré-entraîné chargé avec succès")
    else:
        print("🔧 Entraînement d'un nouveau modèle...")
        
        # Entraîner avec les données réelles si disponibles
        mae, r2 = trainer.train_model(use_real_data=True)
        
        # Sauvegarder le nouveau modèle
        if trainer.save_model():
            print("🎉 Entraînement terminé avec succès!")
        else:
            print("❌ Échec de la sauvegarde du modèle")
    
    print("=" * 50)

if __name__ == "__main__":
    main()