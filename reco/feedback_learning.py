"""
Feedback Learning Service - AI improves from user interactions

This module implements a feedback loop where the AI learns from:
1. Which recommendations users find helpful
2. Which recommendations users actually follow
3. Which categories work best for each user

The more feedback collected, the better the recommendations become!
"""
from django.db.models import Avg, Count, Q
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


def calculate_category_confidence(user, category):
    """
    Calculate ML confidence for a category based on user's past feedback.
    
    The confidence increases when:
    - User marked recommendations as helpful
    - User actually acted on recommendations
    - Recent feedback is weighted more heavily
    
    Args:
        user: User object
        category: Recommendation category (sleep, activity, nutrition, lifestyle)
    
    Returns:
        float: Confidence score between 0.0 and 1.0
    """
    from reco.models import Recommendation
    
    # Get all past recommendations for this user in this category
    past_recos = Recommendation.objects.filter(
        user=user,
        category=category,
        feedback_at__isnull=False  # Only recommendations with feedback
    )
    
    if not past_recos.exists():
        # No feedback yet - return base confidence (40%)
        return 0.40
    
    # Calculate feedback metrics
    total_count = past_recos.count()
    helpful_count = past_recos.filter(helpful=True).count()
    acted_upon_count = past_recos.filter(acted_upon=True).count()
    
    # Calculate scores
    helpful_rate = helpful_count / total_count if total_count > 0 else 0
    action_rate = acted_upon_count / total_count if total_count > 0 else 0
    
    # Weighted confidence calculation
    # - helpful_rate: 60% weight (users find it useful)
    # - action_rate: 40% weight (users actually do it)
    confidence = (helpful_rate * 0.6) + (action_rate * 0.4)
    
    # Apply time decay - recent feedback matters more
    recent_cutoff = timezone.now() - timedelta(days=30)
    recent_recos = past_recos.filter(feedback_at__gte=recent_cutoff)
    
    if recent_recos.exists():
        recent_helpful = recent_recos.filter(helpful=True).count()
        recent_total = recent_recos.count()
        recent_rate = recent_helpful / recent_total if recent_total > 0 else 0
        
        # Boost confidence if recent feedback is positive
        confidence = (confidence * 0.7) + (recent_rate * 0.3)
    
    # Ensure confidence is between 0.1 and 1.0
    confidence = max(0.1, min(1.0, confidence))
    
    # Bonus: If user has acted upon recommendations, boost confidence
    if action_rate > 0.5:  # More than 50% action rate
        confidence = min(1.0, confidence + 0.1)
    
    logger.info(
        f"Category confidence for {user.username}/{category}: "
        f"{confidence:.2%} (helpful: {helpful_count}/{total_count}, "
        f"acted: {acted_upon_count}/{total_count})"
    )
    
    return confidence


def calculate_user_engagement_score(user):
    """
    Calculate overall user engagement score.
    
    Higher engagement = more reliable feedback = better predictions
    
    Returns:
        float: Engagement score between 0.0 and 1.0
    """
    from reco.models import Recommendation
    
    # Get all recommendations for this user
    all_recos = Recommendation.objects.filter(user=user)
    total_recos = all_recos.count()
    
    if total_recos == 0:
        return 0.5  # Neutral score for new users
    
    # Count feedback interactions
    viewed_count = all_recos.filter(viewed=True).count()
    feedback_count = all_recos.filter(feedback_at__isnull=False).count()
    acted_count = all_recos.filter(acted_upon=True).count()
    
    # Calculate engagement rate
    view_rate = viewed_count / total_recos
    feedback_rate = feedback_count / total_recos
    action_rate = acted_count / total_recos
    
    # Weighted engagement score
    engagement = (view_rate * 0.3) + (feedback_rate * 0.4) + (action_rate * 0.3)
    
    logger.info(
        f"User engagement for {user.username}: {engagement:.2%} "
        f"(viewed: {view_rate:.0%}, feedback: {feedback_rate:.0%}, "
        f"actions: {action_rate:.0%})"
    )
    
    return engagement


def get_personalized_confidence(user, category, base_confidence=0.43):
    """
    Get ML confidence adjusted for user's feedback history.
    
    This is the KEY function that makes the AI learn!
    
    Args:
        user: User object
        category: Recommendation category
        base_confidence: Base ML model confidence (default 43%)
    
    Returns:
        float: Personalized confidence score
    """
    # Get category-specific confidence from feedback
    category_confidence = calculate_category_confidence(user, category)
    
    # Get user engagement score
    engagement_score = calculate_user_engagement_score(user)
    
    # CUMULATIVE CONFIDENCE: Base ML + Feedback Learning
    # User wants: 68% base → 75% after feedback → 82% after more feedback → up to 95%
    
    # Calculate feedback boost based on category performance
    # If user likes this category (helpful_rate high), boost goes up
    # Maximum boost: +25% (from 68% base to 93% max)
    feedback_multiplier = category_confidence * engagement_score
    # feedback_multiplier ranges 0.0 to 1.0
    
    # Calculate additive boost (0% to +25%)
    max_boost = 0.25  # Maximum 25% boost
    feedback_boost = feedback_multiplier * max_boost
    
    # Apply cumulative boost to base confidence
    personalized = base_confidence + feedback_boost
    
    # Ensure reasonable bounds (10% to 95%)
    personalized = max(0.10, min(0.95, personalized))
    
    logger.info(
        f"Personalized confidence for {user.username}/{category}: "
        f"{personalized:.2%} (base: {base_confidence:.2%}, "
        f"boost: +{feedback_boost * 100:.1f}%, "
        f"category: {category_confidence:.2%}, engagement: {engagement_score:.2%})"
    )
    
    return personalized


def get_feedback_insights(user):
    """
    Get insights about user's feedback patterns.
    
    Returns:
        dict: Insights for display in UI
    """
    from reco.models import Recommendation
    
    all_recos = Recommendation.objects.filter(user=user)
    feedback_recos = all_recos.filter(feedback_at__isnull=False)
    
    if not feedback_recos.exists():
        return {
            'total_feedback': 0,
            'helpful_rate': 0,
            'action_rate': 0,
            'favorite_category': None,
            'learning_status': 'new',
        }
    
    total_feedback = feedback_recos.count()
    helpful_count = feedback_recos.filter(helpful=True).count()
    acted_count = feedback_recos.filter(acted_upon=True).count()
    
    # Find favorite category (most helpful)
    category_stats = feedback_recos.filter(helpful=True).values('category').annotate(
        count=Count('id')
    ).order_by('-count')
    
    favorite_category = category_stats.first()['category'] if category_stats else None
    
    # Determine learning status
    if total_feedback < 5:
        learning_status = 'learning'
    elif helpful_count / total_feedback > 0.7:
        learning_status = 'excellent'
    elif helpful_count / total_feedback > 0.5:
        learning_status = 'good'
    else:
        learning_status = 'needs_improvement'
    
    # Calculate rates as percentages (0-100) instead of decimals (0.0-1.0)
    helpful_rate = (helpful_count / total_feedback * 100) if total_feedback > 0 else 0
    action_rate = (acted_count / total_feedback * 100) if total_feedback > 0 else 0
    
    return {
        'total_feedback': total_feedback,
        'helpful_rate': helpful_rate,  # Now returns percentage (0-100)
        'action_rate': action_rate,    # Now returns percentage (0-100)
        'favorite_category': favorite_category,
        'learning_status': learning_status,
    }
