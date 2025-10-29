"""
Simulate the ai_progress_view logic to see what data it shows
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'projetPython.settings')
django.setup()

from users.models import CustomUser
from reco.models import Recommendation
from reco.feedback_learning import get_feedback_insights, get_personalized_confidence
from reco.ml_service import get_personalization_service

def test_ai_progress_data():
    user = CustomUser.objects.get(username='hamouda')
    
    print("=" * 70)
    print("AI PROGRESS DASHBOARD DATA - What you should see on the page")
    print("=" * 70)
    
    # Get feedback insights
    feedback_insights = get_feedback_insights(user)
    
    print("\n📊 GLOBAL STATS (Top of page):")
    print(f"   Total Feedbacks: {feedback_insights['total_feedback']}")
    print(f"   Helpful Rate: {feedback_insights['helpful_rate']:.1f}%")
    print(f"   Action Rate: {feedback_insights['action_rate']:.1f}%")
    
    # Calculate confidence for each category
    categories = ['sleep', 'activity', 'nutrition', 'lifestyle']
    ml_service = get_personalization_service()
    
    total_personalized_confidence = 0
    
    print("\n📈 CATEGORY STATS (Progress bars):")
    
    for category in categories:
        # Get base ML confidence
        _, base_ml_confidence, _ = ml_service.predict_helpfulness(user, category)
        
        # Get personalized confidence
        personalized = get_personalized_confidence(user, category, base_ml_confidence)
        
        # Calculate boost
        boost = (personalized - base_ml_confidence) * 100
        
        # Get feedback count
        feedback_count = Recommendation.objects.filter(
            user=user,
            category=category,
            feedback_at__isnull=False
        ).count()
        
        # Get helpful rate
        helpful_count = Recommendation.objects.filter(
            user=user,
            category=category,
            helpful=True
        ).count()
        helpful_rate = (helpful_count / feedback_count * 100) if feedback_count > 0 else 0
        
        icon = {
            'sleep': '😴 Sommeil',
            'activity': '🏃 Activité',
            'nutrition': '🍎 Nutrition',
            'lifestyle': '❤️ Mode de vie'
        }
        
        print(f"\n   {icon[category]}:")
        print(f"      Base ML Confidence: {base_ml_confidence * 100:.1f}%")
        print(f"      Personalized Confidence: {personalized * 100:.1f}%")
        print(f"      Boost from feedback: +{boost:.1f}%")
        print(f"      Feedback count: {feedback_count}")
        print(f"      Helpful rate: {helpful_rate:.1f}%")
        
        total_personalized_confidence += personalized
    
    # Calculate average
    avg_confidence = (total_personalized_confidence / len(categories)) * 100
    boost_potential = 90.0 - avg_confidence
    
    print(f"\n🎯 OVERALL:")
    print(f"   Average Confidence: {avg_confidence:.1f}%")
    print(f"   Boost Potential: +{max(0, boost_potential):.1f}%")
    
    # Learning milestones
    print(f"\n🏆 LEARNING MILESTONES:")
    milestones = [
        (5, "Débutant"),
        (15, "Intermédiaire"),
        (30, "Avancé"),
        (50, "Expert")
    ]
    
    for count, level in milestones:
        status = "✅ Débloqué" if feedback_insights['total_feedback'] >= count else f"🔒 {feedback_insights['total_feedback']}/{count}"
        print(f"   {level} ({count} feedbacks): {status}")
    
    print("\n" + "=" * 70)
    print("✅ Visit http://127.0.0.1:8000/reco/ai-progress/ to see this dashboard!")
    print("=" * 70)

if __name__ == '__main__':
    test_ai_progress_data()
