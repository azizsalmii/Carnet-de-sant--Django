import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import joblib
import os
from django.conf import settings

class AdvancedHealthPredictor:
    """Modèle IA avancé avec capacité d'entraînement"""
    
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.model_path = os.path.join(settings.BASE_DIR, 'journal', 'ml', 'trained_health_model.joblib')
        self.is_trained = False
        self.load_model()
    
    def load_model(self):
        """Charge le modèle entraîné"""
        try:
            if os.path.exists(self.model_path):
                self.model = joblib.load(self.model_path)
                self.is_trained = True
                print("✅ Modèle IA chargé avec succès")
            else:
                print("❌ Aucun modèle entraîné trouvé, utilisation du modèle par défaut")
                self._create_default_model()
        except Exception as e:
            print(f"❌ Erreur chargement modèle: {e}")
            self._create_default_model()
    
    def _create_default_model(self):
        """Crée un modèle par défaut basé sur des règles"""
        self.model = None
        self.is_trained = False
    
    def predict_health_score(self, features_dict):
        """Prédit le score de santé"""
        if not self.is_trained or self.model is None:
            return self._fallback_prediction(features_dict)
        
        try:
            # Préparer les features
            features = np.array([[
                features_dict.get('sleep_duration', 7),
                features_dict.get('sleep_quality', 3),
                features_dict.get('steps_count', 5000),
                features_dict.get('exercise_duration', 30),
                features_dict.get('pain_level', 3),
                features_dict.get('medication_adherence', 1)
            ]])
            
            # Prédiction
            prediction = self.model.predict(features)[0]
            return max(0, min(100, prediction))
            
        except Exception as e:
            print(f"❌ Erreur prédiction IA: {e}")
            return self._fallback_prediction(features_dict)
    
    def _fallback_prediction(self, features_dict):
        """Prédiction de fallback basée sur des règles"""
        score = 100
        
        # Logique basée sur des règles expertes
        sleep_duration = features_dict.get('sleep_duration', 7)
        if sleep_duration < 6 or sleep_duration > 9:
            score -= 20
        elif sleep_duration < 7 or sleep_duration > 8:
            score -= 10
        
        sleep_quality = features_dict.get('sleep_quality', 3)
        if sleep_quality < 3:
            score -= 15
        elif sleep_quality < 4:
            score -= 5
        
        steps_count = features_dict.get('steps_count', 5000)
        if steps_count < 5000:
            score -= 15
        elif steps_count < 7500:
            score -= 5
        
        pain_level = features_dict.get('pain_level', 3)
        if pain_level > 5:
            score -= (pain_level - 5) * 5
        
        medication_adherence = features_dict.get('medication_adherence', 1)
        if not medication_adherence:
            score -= 10
        
        return max(50, score)