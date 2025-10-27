"""
Example ML model implementation using simple rule-based scoring.

This demonstrates how to create a trainable model that learns
from user feedback to improve recommendation relevance.
"""
from typing import Dict, List
from collections import defaultdict
import logging

from .base import BaseRecommendationModel

logger = logging.getLogger(__name__)


class FeedbackWeightedModel(BaseRecommendationModel):
    """
    Simple ML model that learns weights from user feedback.
    
    Uses feedback to weight different recommendation categories
    and features for personalized recommendations.
    """
    
    def __init__(self):
        super().__init__(model_id='feedback_weighted', version='1.0.0')
        self.category_weights = {
            'activity': 1.0,
            'nutrition': 1.0,
            'sleep': 1.0,
            'lifestyle': 1.0,
        }
        self.feature_importance = {}
        self.trained = False
    
    def train(self, features: List[Dict], labels: List[Dict]) -> Dict:
        """
        Train model by learning from helpful vs unhelpful recommendations.
        
        Args:
            features: List of user feature dictionaries
            labels: List of label dictionaries with helpful_recommendations
            
        Returns:
            Training metrics
        """
        if not features or not labels:
            return {'error': 'Insufficient training data'}
        
        logger.info(f"Training {self.model_id} on {len(features)} samples")
        
        # Count helpful/unhelpful by category
        category_helpful = defaultdict(int)
        category_total = defaultdict(int)
        
        for label in labels:
            helpful = label.get('helpful_recommendations', [])
            unhelpful = label.get('unhelpful_recommendations', [])
            
            for rec in helpful:
                category_helpful[rec['category']] += 1
                category_total[rec['category']] += 1
            
            for rec in unhelpful:
                category_total[rec['category']] += 1
        
        # Compute category weights based on helpful ratio
        for category in self.category_weights:
            total = category_total.get(category, 0)
            if total > 0:
                helpful_ratio = category_helpful[category] / total
                # Weight: helpful ratio * 2 (so 50% helpful = 1.0 weight)
                self.category_weights[category] = helpful_ratio * 2
            else:
                self.category_weights[category] = 1.0
        
        # Learn feature importance from feature statistics
        feature_sums = defaultdict(float)
        feature_counts = defaultdict(int)
        
        for feat_dict in features:
            for key, value in feat_dict.items():
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    feature_sums[key] += value
                    feature_counts[key] += 1
        
        # Compute average feature values
        self.feature_importance = {
            key: feature_sums[key] / feature_counts[key]
            for key in feature_sums
            if feature_counts[key] > 0
        }
        
        self.trained = True
        
        from datetime import datetime
        self.trained_at = datetime.now()
        self.metadata = {
            'training_samples': len(features),
            'category_weights': self.category_weights,
            'num_features': len(self.feature_importance),
        }
        
        return {
            'status': 'success',
            'samples': len(features),
            'category_weights': self.category_weights,
            'features_learned': len(self.feature_importance),
        }
    
    def predict(self, features: Dict) -> List[Dict]:
        """
        Generate recommendations based on learned weights.
        
        Args:
            features: Feature dictionary for one user
            
        Returns:
            List of recommendations sorted by score
        """
        if not self.trained:
            logger.warning("Model not trained, using default weights")
        
        recommendations = []
        
        # Activity recommendation
        steps_avg = features.get('steps_7d_mean', 0)
        if steps_avg < 5000:
            score = self.category_weights['activity'] * 0.6
            recommendations.append({
                'category': 'activity',
                'text': 'Augmentez progressivement votre activité avec une marche de 15-20 minutes par jour.',
                'score': score,
            })
        elif steps_avg >= 8000:
            score = self.category_weights['activity'] * 0.3
            recommendations.append({
                'category': 'activity',
                'text': 'Excellent ! Maintenez votre niveau d\'activité actuel.',
                'score': score,
            })
        
        # Sleep recommendation
        sleep_avg = features.get('sleep_7d_mean', 0)
        if sleep_avg > 0 and sleep_avg < 6.5:
            score = self.category_weights['sleep'] * 0.65
            recommendations.append({
                'category': 'sleep',
                'text': 'Essayez d\'établir une routine de coucher régulière pour améliorer la qualité du sommeil.',
                'score': score,
            })
        elif sleep_avg >= 7.5:
            score = self.category_weights['sleep'] * 0.3
            recommendations.append({
                'category': 'sleep',
                'text': 'Votre sommeil est excellent, continuez vos bonnes habitudes.',
                'score': score,
            })
        
        # BP recommendation
        bp_category = features.get('bp_category', '')
        if bp_category in ['stage1_hypertension', 'stage2_hypertension', 'hypertensive_crisis']:
            score = self.category_weights['lifestyle'] * 0.95
            recommendations.append({
                'category': 'lifestyle',
                'text': 'Consultez un professionnel de santé concernant votre tension artérielle.',
                'score': score,
            })
        elif bp_category == 'normal':
            score = self.category_weights['lifestyle'] * 0.2
            recommendations.append({
                'category': 'lifestyle',
                'text': 'Votre tension artérielle est dans la norme, excellente santé cardiovasculaire.',
                'score': score,
            })
        
        # Consistency recommendation
        consistency = features.get('steps_consistency', 0)
        if consistency < 0.6:
            score = self.category_weights['lifestyle'] * 0.4
            recommendations.append({
                'category': 'lifestyle',
                'text': 'Essayez d\'établir une routine d\'activité plus régulière pour de meilleurs résultats.',
                'score': score,
            })
        
        # Sort by score descending
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        
        return recommendations[:5]  # Top 5 recommendations
    
    def evaluate(self, features: List[Dict], labels: List[Dict]) -> Dict:
        """
        Evaluate model on test data.
        
        Uses the ModelEvaluator from base.py for standard metrics.
        """
        from .base import ModelEvaluator
        
        # Generate predictions for each user
        predictions_by_user = {}
        ground_truth_by_user = {}
        
        for i, feat_dict in enumerate(features):
            user_id = feat_dict.get('user_id', i)
            predictions_by_user[user_id] = self.predict(feat_dict)
            
            if i < len(labels):
                ground_truth_by_user[user_id] = labels[i].get('helpful_recommendations', [])
        
        # Use standard evaluator
        metrics = ModelEvaluator.evaluate_model(predictions_by_user, ground_truth_by_user)
        
        return metrics
    
    def _get_model_state(self) -> Dict:
        """Get model state for serialization."""
        return {
            'category_weights': self.category_weights,
            'feature_importance': self.feature_importance,
            'trained': self.trained,
        }
    
    def _set_model_state(self, state: Dict):
        """Set model state from deserialization."""
        self.category_weights = state.get('category_weights', self.category_weights)
        self.feature_importance = state.get('feature_importance', {})
        self.trained = state.get('trained', False)


# Example usage in comments:
"""
# Training example
from reco.ml.example_model import FeedbackWeightedModel
from reco.ml.base import TrainingDataset

# Load training data
train_ds = TrainingDataset.load('training_data/train.json')

# Create and train model
model = FeedbackWeightedModel()
metrics = model.train(train_ds.features, train_ds.labels)
print(f"Training metrics: {metrics}")

# Save model
from pathlib import Path
model.save(Path('models/feedback_weighted_v1.json'))

# Later, load and use
model = FeedbackWeightedModel()
model.load(Path('models/feedback_weighted_v1.json'))

# Generate recommendations for a user
user_features = FeatureEngineer.compute_comprehensive_features(user_id=1)
recommendations = model.predict(user_features)

# Evaluate on validation set
val_ds = TrainingDataset.load('training_data/validation.json')
eval_metrics = model.evaluate(val_ds.features, val_ds.labels)
print(f"Evaluation: {eval_metrics}")
"""
