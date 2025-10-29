"""
ML-powered personalization service for health recommendations.

This service loads the trained ML model and uses it to:
1. Predict which recommendations will be helpful for each user
2. Rank recommendations by predicted helpfulness
3. Filter out low-confidence recommendations
4. Provide explanation for why each recommendation is suggested
"""
import logging
from pathlib import Path
import joblib
from datetime import timedelta
from django.conf import settings
from django.utils import timezone

# Optional numpy import - gracefully handle if not installed (production minimal requirements)
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("numpy not available - ML features will be disabled")

logger = logging.getLogger(__name__)


class PersonalizationService:
    """
    Service for ML-powered personalized recommendations.
    """
    
    def __init__(self):
        self.model = None
        self.model_version = None
        self.model_path = Path(settings.BASE_DIR) / "models" / "v1"
        self._load_model()
    
    def _load_model(self):
        """Load the trained ML model."""
        # Skip model loading if numpy is not available (minimal production requirements)
        if not NUMPY_AVAILABLE:
            logger.info("⚠️ Skipping ML model load - numpy not installed (minimal production mode)")
            return
            
        try:
            # Priorité au modèle calibré si disponible
            calibrated_file = self.model_path / "model_calibrated.joblib"
            model_file = self.model_path / "model.joblib"
            scaler_file = self.model_path / "scaler.joblib"
            
            if calibrated_file.exists():
                logger.info("🎯 Chargement du modèle calibré...")
                self.model = joblib.load(calibrated_file)
                # Charge le scaler séparément car calibrated model n'inclut pas le scaler
                if scaler_file.exists():
                    self.scaler = joblib.load(scaler_file)
                else:
                    # Fallback: charge depuis model.joblib si c'est un dict
                    if model_file.exists():
                        loaded_data = joblib.load(model_file)
                        if isinstance(loaded_data, dict):
                            self.scaler = loaded_data.get('scaler')
                
                self.model_version = "v1-calibrated"
                logger.info(f"✅ ML model calibré chargé: {self.model_version}")
                
            elif model_file.exists():
                loaded_data = joblib.load(model_file)
                # Check if it's a dict containing model and scaler
                if isinstance(loaded_data, dict):
                    self.model = loaded_data.get('model')
                    self.scaler = loaded_data.get('scaler')
                else:
                    # Direct model object
                    self.model = loaded_data
                
                self.model_version = "v1"
                logger.info(f"ML model loaded successfully: {self.model_version}")
                logger.info(f"Model type: {type(self.model)}")
            else:
                logger.warning("No trained model found. Using rule-based recommendations only.")
        except Exception as e:
            logger.error(f"Error loading ML model: {e}")
            self.model = None
    
    def compute_ml_features(self, user):
        """
        Compute comprehensive features for ML prediction.
        
        Args:
            user: Django User object
            
        Returns:
            dict: Feature dictionary for ML model
        """
        from .models import DailyMetrics
        
        # Get metrics for different time windows
        now = timezone.now().date()
        metrics_7d = DailyMetrics.objects.filter(
            user=user,
            date__gte=now - timedelta(days=7)
        ).order_by('-date')
        
        metrics_14d = DailyMetrics.objects.filter(
            user=user,
            date__gte=now - timedelta(days=14)
        ).order_by('-date')
        
        features = {}
        
        # 7-day features
        sleep_7d = [m.sleep_hours for m in metrics_7d if m.sleep_hours is not None]
        steps_7d = [m.steps for m in metrics_7d if m.steps is not None]
        sbp_7d = [m.systolic_bp for m in metrics_7d if m.systolic_bp is not None]
        dbp_7d = [m.diastolic_bp for m in metrics_7d if m.diastolic_bp is not None]
        
        features['steps_7d_mean'] = np.mean(steps_7d) if steps_7d else 0
        features['steps_7d_std'] = np.std(steps_7d) if len(steps_7d) > 1 else 0
        features['sleep_7d_mean'] = np.mean(sleep_7d) if sleep_7d else 0
        features['sleep_7d_std'] = np.std(sleep_7d) if len(sleep_7d) > 1 else 0
        features['sbp_7d_mean'] = np.mean(sbp_7d) if sbp_7d else 0
        features['dbp_7d_mean'] = np.mean(dbp_7d) if dbp_7d else 0
        
        # 14-day features
        sleep_14d = [m.sleep_hours for m in metrics_14d if m.sleep_hours is not None]
        steps_14d = [m.steps for m in metrics_14d if m.steps is not None]
        
        features['steps_14d_mean'] = np.mean(steps_14d) if steps_14d else 0
        features['sleep_14d_mean'] = np.mean(sleep_14d) if sleep_14d else 0
        
        # Consistency features (coefficient of variation)
        features['sleep_consistency'] = (
            features['sleep_7d_std'] / features['sleep_7d_mean']
            if features['sleep_7d_mean'] > 0 else 0
        )
        features['steps_consistency'] = (
            features['steps_7d_std'] / features['steps_7d_mean']
            if features['steps_7d_mean'] > 0 else 0
        )
        
        # Trend features (comparing recent 7d vs 14d)
        features['sleep_trend'] = (
            features['sleep_7d_mean'] - features['sleep_14d_mean']
            if features['sleep_14d_mean'] > 0 else 0
        )
        features['steps_trend'] = (
            features['steps_7d_mean'] - features['steps_14d_mean']
            if features['steps_14d_mean'] > 0 else 0
        )
        
        # Health risk indicators
        features['bp_risk'] = 1 if features['sbp_7d_mean'] > 130 else 0
        features['low_activity_risk'] = 1 if features['steps_7d_mean'] < 5000 else 0
        features['sleep_deprivation_risk'] = 1 if features['sleep_7d_mean'] < 6 else 0
        
        # Data completeness
        features['data_completeness'] = (len(sleep_7d) + len(steps_7d)) / 14.0
        
        return features
    
    def predict_helpfulness(self, user, recommendation_category):
        """
        Predict if a recommendation will be helpful for this user.
        
        Args:
            user: Django User object
            recommendation_category: str, category of recommendation
            
        Returns:
            tuple: (is_helpful: bool, confidence: float, explanation: str)
        """
        if not self.model:
            # Fallback: all recommendations are considered helpful
            return True, 0.5, "Using rule-based recommendations (no ML model loaded)"
        
        try:
            # Compute features
            features = self.compute_ml_features(user)
            
            # Prepare feature vector (must match training order)
            feature_vector = np.array([[
                features.get('steps_7d_mean', 0),
                features.get('steps_7d_std', 0),
                features.get('steps_14d_mean', 0),
                features.get('sleep_7d_mean', 0),
                features.get('sleep_7d_std', 0),
                features.get('sleep_14d_mean', 0),
                features.get('sbp_7d_mean', 0),
                features.get('dbp_7d_mean', 0),
                features.get('sleep_consistency', 0),
                features.get('steps_consistency', 0),
                features.get('sleep_trend', 0),
                features.get('steps_trend', 0),
                features.get('bp_risk', 0),
                features.get('low_activity_risk', 0),
                features.get('sleep_deprivation_risk', 0),
                features.get('data_completeness', 0),
            ]])
            
            # Scale features if scaler is available
            if self.scaler:
                feature_vector = self.scaler.transform(feature_vector)
            
            # Predict
            prediction = self.model.predict(feature_vector)[0]
            proba = self.model.predict_proba(feature_vector)[0]
            # Get confidence for positive class (helpful=1)
            confidence = float(proba[1]) if len(proba) > 1 else float(proba[0])
            
            # Generate explanation
            explanation = self._generate_explanation(features, recommendation_category, confidence)
            
            return bool(prediction), float(confidence), explanation
            
        except Exception as e:
            logger.error(f"Error predicting helpfulness: {e}")
            return True, 0.5, "Prediction unavailable, using default"
    
    def _generate_explanation(self, features, category, confidence):
        """
        Generate human-readable explanation for why this recommendation was given.
        
        Args:
            features: dict of user features
            category: recommendation category
            confidence: ML confidence score
            
        Returns:
            str: Explanation text
        """
        explanations = []
        
        # Sleep-related explanations
        if category in ['sleep', 'lifestyle']:
            sleep_avg = features.get('sleep_7d_mean', 0)
            if sleep_avg < 6:
                explanations.append(f"Votre sommeil moyen est faible ({sleep_avg:.1f}h)")
            elif sleep_avg > 9:
                explanations.append(f"Votre sommeil est excessif ({sleep_avg:.1f}h)")
            
            sleep_consistency = features.get('sleep_consistency', 0)
            if sleep_consistency > 0.3:
                explanations.append("Votre horaire de sommeil est irrégulier")
        
        # Activity-related explanations
        if category in ['activity', 'lifestyle']:
            steps_avg = features.get('steps_7d_mean', 0)
            if steps_avg < 5000:
                explanations.append(f"Votre activité est faible ({int(steps_avg)} pas/jour)")
            
            steps_trend = features.get('steps_trend', 0)
            if steps_trend < -1000:
                explanations.append("Votre activité diminue récemment")
        
        # Blood pressure explanations
        if features.get('bp_risk', 0) == 1:
            sbp = features.get('sbp_7d_mean', 0)
            explanations.append(f"Tension artérielle élevée (SBP: {sbp:.0f})")
        
        # Data quality note
        completeness = features.get('data_completeness', 0)
        if completeness < 0.5:
            explanations.append("Données limitées - enregistrez plus de métriques pour de meilleurs conseils")
        
        # Add confidence indicator
        if confidence > 0.8:
            explanations.append(f"✓ Fortement personnalisé pour vous ({confidence*100:.0f}%)")
        elif confidence > 0.6:
            explanations.append(f"Personnalisé pour votre profil ({confidence*100:.0f}%)")
        
        return " • ".join(explanations) if explanations else "Recommandation basée sur vos données de santé"
    
    def rank_recommendations(self, user, recommendations):
        """
        Rank recommendations by predicted helpfulness.
        
        Args:
            user: Django User object
            recommendations: list of Recommendation objects
            
        Returns:
            list: Recommendations sorted by ML-predicted helpfulness
        """
        if not self.model or not recommendations:
            return recommendations
        
        # Predict for each recommendation
        scored_recos = []
        for reco in recommendations:
            is_helpful, confidence, explanation = self.predict_helpfulness(user, reco.category)
            reco.ml_confidence = confidence
            reco.ml_explanation = explanation
            scored_recos.append((confidence, reco))
        
        # Sort by confidence (highest first)
        scored_recos.sort(key=lambda x: x[0], reverse=True)
        
        return [reco for _, reco in scored_recos]


# Global instance
_personalization_service = None

def get_personalization_service():
    """Get the global personalization service instance."""
    global _personalization_service
    if _personalization_service is None:
        _personalization_service = PersonalizationService()
    return _personalization_service
