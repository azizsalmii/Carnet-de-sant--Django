"""
Service layer for computing features and generating recommendations.
"""
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db.models import Q
from .models import DailyMetrics, Recommendation
from .engine import rules
from .ml_service import get_personalization_service
import logging
from django.contrib.auth import get_user_model

User = get_user_model()
logger = logging.getLogger(__name__)


def compute_features_for_user(user_id):
    """
    Compute features for a given user based on their metrics.
    
    Returns a dict with:
    - sleep_7d_avg: Average sleep hours over last 7 days
    - steps_7d_avg: Average steps over last 7 days
    - latest_sbp: Most recent systolic blood pressure
    - latest_dbp: Most recent diastolic blood pressure
    """
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return {}
    
    # Get last 7 days of metrics
    seven_days_ago = timezone.now().date() - timedelta(days=7)
    recent_metrics = DailyMetrics.objects.filter(
        user=user,
        date__gte=seven_days_ago
    ).order_by('-date')
    
    features = {
        'sleep_7d_avg': 0.0,
        'steps_7d_avg': 0.0,
        'latest_sbp': 0,
        'latest_dbp': 0,
    }
    
    if not recent_metrics.exists():
        return features
    
    # Compute averages
    sleep_values = [m.sleep_hours for m in recent_metrics if m.sleep_hours is not None]
    steps_values = [m.steps for m in recent_metrics if m.steps is not None]
    
    if sleep_values:
        features['sleep_7d_avg'] = sum(sleep_values) / len(sleep_values)
    
    if steps_values:
        features['steps_7d_avg'] = sum(steps_values) / len(steps_values)
    
    # Get latest blood pressure
    latest = recent_metrics.first()
    if latest:
        features['latest_sbp'] = latest.systolic_bp or 0
        features['latest_dbp'] = latest.diastolic_bp or 0
    
    return features


def generate_recommendations_for_user(user_id, features):
    """
    Generate ML-powered personalized recommendations for a user.
    
    This function:
    1. Deletes old recommendations for the user
    2. Applies rule-based engine to generate candidate recommendations
    3. Uses ML model to predict which recommendations will be helpful
    4. Ranks recommendations by ML confidence scores
    5. Adds personalized explanations
    
    Args:
        user_id: User ID
        features: Dict of computed features from compute_features_for_user()
    
    Returns:
        Number of recommendations created
    """
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return 0
    
    # Get old recommendations BEFORE deleting (for learning from past feedback)
    old_recommendations = list(Recommendation.objects.filter(user=user))
    old_texts = set(r.text for r in old_recommendations)
    
    # Find which categories the user liked (helpful=True or acted_upon=True)
    liked_categories = [
        r.category for r in old_recommendations 
        if r.helpful is True or r.acted_upon is True
    ]
    liked_categories = list(set(liked_categories))  # Remove duplicates
    
    # Delete ONLY recommendations WITHOUT feedback (keep the learning history!)
    # This preserves user feedback for the AI progress dashboard
    recommendations_without_feedback = Recommendation.objects.filter(
        user=user,
        feedback_at__isnull=True  # Only delete if no feedback given
    )
    deleted_count = recommendations_without_feedback.delete()[0]
    if deleted_count > 0:
        logger.info(f"Deleted {deleted_count} old recommendations WITHOUT feedback for {user.username}")
    
    # Count kept recommendations with feedback
    kept_count = Recommendation.objects.filter(user=user, feedback_at__isnull=False).count()
    if kept_count > 0:
        logger.info(f"Kept {kept_count} recommendations WITH feedback for learning")
    
    # Get ML personalization service
    ml_service = get_personalization_service()
    
    # Apply all rules to generate candidate recommendations
    rule_functions = rules()
    candidate_recommendations = []
    
    for rule_func in rule_functions:
        result = rule_func(features)
        if result:
            # Create recommendation object (not saved yet)
            reco = Recommendation(
                user=user,
                category=result['category'],
                text=result['text'],
                score=result['score'],
                rationale=str(features),
                source='rule',
            )
            candidate_recommendations.append(reco)
    
    if not candidate_recommendations:
        return 0
    
    # Use ML to filter and rank recommendations
    personalized_recommendations = []
    
    # Import feedback learning service
    from .feedback_learning import get_personalized_confidence, get_feedback_insights
    
    # Get user's past feedback to learn preferences
    feedback_insights = get_feedback_insights(user)
    
    logger.info(
        f"Generating personalized recommendations for {user.username}: "
        f"Past recommendations: {len(old_recommendations)}, "
        f"Liked categories: {liked_categories}, "
        f"Learning status: {feedback_insights['learning_status']}"
    )
    
    for reco in candidate_recommendations:
        # Skip if we already gave this exact recommendation
        if reco.text in old_texts:
            logger.info(f"Skipping duplicate: {reco.text[:50]}...")
            continue
        
        # Get base ML prediction
        _, base_confidence, explanation = ml_service.predict_helpfulness(user, reco.category)
        
        # Apply feedback learning to improve confidence
        # Note: base_confidence is already 0.0-1.0 from ML model
        personalized_confidence = get_personalized_confidence(
            user=user,
            category=reco.category,
            base_confidence=base_confidence  # Already in 0.0-1.0 range
        )
        
        # Boost confidence if this category was liked before
        if reco.category in liked_categories:
            personalized_confidence = min(0.95, personalized_confidence * 1.2)  # +20% boost
            logger.info(f"Boosting {reco.category} (user liked this category before)")
        
        # Convert back to percentage
        final_confidence = personalized_confidence * 100
        
        # Only keep recommendations with >10% confidence
        if final_confidence > 10.0:
            # Update recommendation with personalized ML insights
            reco.score = personalized_confidence  # Store as 0.0-1.0
            reco.rationale = explanation  # Add personalized explanation
            reco.source = 'ml' if ml_service.model else 'rule'
            reco.model_version = ml_service.model_version or 'rule-only'
            personalized_recommendations.append(reco)
            
            logger.info(
                f"New recommendation: {reco.category} "
                f"(base: {base_confidence*100:.0f}%, personalized: {final_confidence:.0f}%)"
            )
    
    # Sort by ML confidence (highest first)
    personalized_recommendations.sort(key=lambda r: r.score, reverse=True)
    
    # Bulk create recommendations
    if personalized_recommendations:
        Recommendation.objects.bulk_create(personalized_recommendations)
        logger.info(
            f"Created {len(personalized_recommendations)} personalized recommendations "
            f"for {user.username} (filtered from {len(candidate_recommendations)} candidates)"
        )
    
    return len(personalized_recommendations)
