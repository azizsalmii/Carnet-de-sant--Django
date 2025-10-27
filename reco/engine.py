"""
Recommendation engine with rule-based logic.

Pure Python implementation without external ML dependencies.
Rules generate safe, generic lifestyle recommendations with multiple variations.
"""
import random
from .rule_variations import (
    get_sleep_recommendations,
    get_activity_recommendations,
    get_bp_high_recommendations,
    get_bp_moderate_recommendations,
    get_stress_recommendations,
    get_hydration_recommendations,
    get_nutrition_recommendations,
    get_morning_sunlight_recommendations,
    get_schedule_recommendations,
    get_standing_breaks_recommendations,
)


def rules():
    """
    Return a list of rule functions that generate recommendations.
    
    Each rule is a callable that takes features dict and returns
    a recommendation dict or None if the rule doesn't apply.
    
    Recommendation dict structure:
    {
        'category': str,  # 'activity', 'nutrition', 'sleep', 'lifestyle'
        'text': str,      # The recommendation text
        'score': float,   # Priority/relevance score (0.0-1.0)
    }
    """
    
    def sleep_short(features):
        """Recommend better sleep hygiene if average sleep is low."""
        sleep_avg = features.get('sleep_7d_avg', 0)
        if sleep_avg > 0 and sleep_avg < 6.0:
            # Pick a random variation to avoid repetition
            text = random.choice(get_sleep_recommendations())
            return {
                'category': 'sleep',
                'text': text,
                'score': 0.6,
            }
        return None
    
    def steps_low(features):
        """Recommend light activity if step count is low."""
        steps_avg = features.get('steps_7d_avg', 0)
        if steps_avg > 0 and steps_avg < 5000:
            # Pick a random variation
            text = random.choice(get_activity_recommendations())
            return {
                'category': 'activity',
                'text': text,
                'score': 0.55,
            }
        return None
    
    def bp_alert_critical(features):
        """Critical alert if blood pressure is dangerously high."""
        latest_sbp = features.get('latest_sbp', 0)
        latest_dbp = features.get('latest_dbp', 0)
        
        if latest_sbp >= 180 or latest_dbp >= 120:
            return {
                'category': 'lifestyle',
                'text': 'Votre tension artérielle est très élevée. Consultez immédiatement un professionnel de santé.',
                'score': 1.0,
            }
        return None
    
    def bp_alert_high(features):
        """Alert if blood pressure is elevated (stage 2 hypertension)."""
        latest_sbp = features.get('latest_sbp', 0)
        latest_dbp = features.get('latest_dbp', 0)
        
        if latest_sbp >= 140 or latest_dbp >= 90:
            # Pick a random variation
            text = random.choice(get_bp_high_recommendations())
            return {
                'category': 'lifestyle',
                'text': text,
                'score': 0.85,
            }
        return None
    
    def bp_alert_moderate(features):
        """Alert if blood pressure is moderately elevated."""
        latest_sbp = features.get('latest_sbp', 0)
        latest_dbp = features.get('latest_dbp', 0)
        
        if latest_sbp >= 130 or latest_dbp >= 80:
            # Pick a random variation
            text = random.choice(get_bp_moderate_recommendations())
            return {
                'category': 'lifestyle',
                'text': text,
                'score': 0.7,
            }
        return None
    
    def sleep_good(features):
        """Positive reinforcement for good sleep habits."""
        sleep_avg = features.get('sleep_7d_avg', 0)
        if sleep_avg >= 7.0:
            return {
                'category': 'sleep',
                'text': 'Bravo ! Vous maintenez de bonnes habitudes de sommeil. Continuez comme ça.',
                'score': 0.3,
            }
        return None
    
    def steps_good(features):
        """Positive reinforcement for good activity levels."""
        steps_avg = features.get('steps_7d_avg', 0)
        if steps_avg >= 8000:
            return {
                'category': 'activity',
                'text': 'Excellent niveau d\'activité ! Vous atteignez les objectifs recommandés.',
                'score': 0.3,
            }
        return None
    
    def hydration_reminder(features):
        """Encourage proper hydration."""
        steps_avg = features.get('steps_7d_avg', 0)
        if steps_avg > 0:  # Always suggest for active users
            text = random.choice(get_hydration_recommendations())
            return {
                'category': 'nutrition',
                'text': text,
                'score': 0.4,
            }
        return None
    
    def stress_management(features):
        """Suggest stress management techniques."""
        sleep_avg = features.get('sleep_7d_avg', 0)
        if sleep_avg < 7.0:  # Poor sleep often indicates stress
            text = random.choice(get_stress_recommendations())
            return {
                'category': 'lifestyle',
                'text': text,
                'score': 0.5,
            }
        return None
    
    def morning_sunlight(features):
        """Recommend morning sunlight exposure."""
        sleep_avg = features.get('sleep_7d_avg', 0)
        if sleep_avg < 7.0:
            text = random.choice(get_morning_sunlight_recommendations())
            return {
                'category': 'sleep',
                'text': text,
                'score': 0.45,
            }
        return None
    
    def balanced_meals(features):
        """Encourage balanced nutrition."""
        text = random.choice(get_nutrition_recommendations())
        return {
            'category': 'nutrition',
            'text': text,
            'score': 0.4,
        }
    
    def regular_schedule(features):
        """Encourage consistent sleep schedule."""
        sleep_avg = features.get('sleep_7d_avg', 0)
        if sleep_avg < 7.0:
            text = random.choice(get_schedule_recommendations())
            return {
                'category': 'sleep',
                'text': text,
                'score': 0.5,
            }
        return None
    
    def standing_breaks(features):
        """Encourage movement breaks."""
        steps_avg = features.get('steps_7d_avg', 0)
        if steps_avg < 8000:
            text = random.choice(get_standing_breaks_recommendations())
            return {
                'category': 'activity',
                'text': text,
                'score': 0.45,
            }
        return None
    
    return [
        bp_alert_critical,      # Highest priority (180/120+)
        bp_alert_high,          # High BP (140/90+)
        bp_alert_moderate,      # Moderate BP (130/80+)
        sleep_short,            # Poor sleep
        regular_schedule,       # Sleep schedule
        morning_sunlight,       # Circadian rhythm
        steps_low,              # Low activity
        standing_breaks,        # Movement breaks
        stress_management,      # Stress reduction
        hydration_reminder,     # Hydration
        balanced_meals,         # Nutrition
        sleep_good,             # Positive reinforcement
        steps_good,             # Positive reinforcement
    ]
