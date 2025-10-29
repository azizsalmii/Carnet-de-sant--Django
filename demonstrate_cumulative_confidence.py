"""
Demonstrate how confidence ACCUMULATES with each feedback cycle
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'projetPython.settings')
django.setup()

from users.models import CustomUser
from reco.models import Recommendation
from reco.services import generate_recommendations_for_user, compute_features_for_user
from reco.ml_service import get_personalization_service
from reco.feedback_learning import get_personalized_confidence
from django.utils import timezone
from django.db.models import Avg

def simulate_feedback_cycles():
    user = CustomUser.objects.get(username='hamouda')
    ml_service = get_personalization_service()
    
    print("=" * 70)
    print("CUMULATIVE CONFIDENCE DEMONSTRATION")
    print("=" * 70)
    
    # Get base ML confidence
    _, base_ml_conf, _ = ml_service.predict_helpfulness(user, 'nutrition')
    
    print(f"\n📊 STARTING POINT:")
    print(f"   Base ML Confidence (nutrition): {base_ml_conf * 100:.1f}%")
    print(f"   Current feedback count: {Recommendation.objects.filter(user=user, feedback_at__isnull=False).count()}")
    
    cycles = [
        ("Cycle 1: Give feedback on 3 recommendations", 3),
        ("Cycle 2: Give feedback on 3 more recommendations", 3),
        ("Cycle 3: Give feedback on 3 more recommendations", 3),
        ("Cycle 4: Give feedback on 3 more recommendations", 3),
    ]
    
    for cycle_name, feedback_count in cycles:
        print(f"\n{'=' * 70}")
        print(f"🔄 {cycle_name}")
        print(f"{'=' * 70}")
        
        # Get recommendations without feedback
        recos_to_feedback = Recommendation.objects.filter(
            user=user,
            feedback_at__isnull=True,
            category='nutrition'
        )[:feedback_count]
        
        if recos_to_feedback.count() < feedback_count:
            print(f"\n⚠️ Not enough recommendations. Generating new ones...")
            features = compute_features_for_user(user.id)
            new_count = generate_recommendations_for_user(user.id, features)
            print(f"   Generated {new_count} new recommendations")
            
            # Get again
            recos_to_feedback = Recommendation.objects.filter(
                user=user,
                feedback_at__isnull=True,
                category='nutrition'
            )[:feedback_count]
        
        # Give positive feedback
        feedback_given = 0
        for reco in recos_to_feedback:
            reco.helpful = True
            reco.acted_upon = True
            reco.feedback_at = timezone.now()
            reco.save()
            feedback_given += 1
        
        print(f"\n✅ Gave {feedback_given} positive feedbacks to nutrition category")
        
        # Calculate new confidence
        personalized_conf = get_personalized_confidence(user, 'nutrition', base_ml_conf)
        
        # Get stats
        nutrition_recos = Recommendation.objects.filter(user=user, category='nutrition')
        nutrition_feedback = nutrition_recos.filter(feedback_at__isnull=False)
        helpful_count = nutrition_feedback.filter(helpful=True).count()
        
        boost = (personalized_conf - base_ml_conf) * 100
        
        print(f"\n📈 RESULTS:")
        print(f"   Total nutrition feedbacks: {nutrition_feedback.count()}")
        print(f"   Marked helpful: {helpful_count}")
        print(f"   Base confidence: {base_ml_conf * 100:.1f}%")
        print(f"   Personalized confidence: {personalized_conf * 100:.1f}%")
        print(f"   🚀 Boost: +{boost:.1f}% points")
        
        if personalized_conf * 100 >= 85:
            print(f"\n🎉 GOAL REACHED! Confidence is now {personalized_conf * 100:.1f}%")
            break
    
    # Final summary
    print(f"\n{'=' * 70}")
    print("📊 FINAL SUMMARY")
    print(f"{'=' * 70}")
    
    all_feedback = Recommendation.objects.filter(user=user, feedback_at__isnull=False)
    
    print(f"\nTotal feedbacks given: {all_feedback.count()}")
    print(f"Marked helpful: {all_feedback.filter(helpful=True).count()}")
    print(f"Acted upon: {all_feedback.filter(acted_upon=True).count()}")
    
    print(f"\n🏆 CONFIDENCE BY CATEGORY:")
    for category in ['sleep', 'activity', 'nutrition', 'lifestyle']:
        _, base, _ = ml_service.predict_helpfulness(user, category)
        personalized = get_personalized_confidence(user, category, base)
        boost = (personalized - base) * 100
        
        icon = {'sleep': '😴', 'activity': '🏃', 'nutrition': '🍎', 'lifestyle': '❤️'}
        print(f"   {icon[category]} {category}: {personalized * 100:.1f}% (base: {base * 100:.1f}%, boost: +{boost:.1f}%)")
    
    print(f"\n✅ Refresh http://127.0.0.1:8000/reco/ai-progress/ to see updated dashboard!")
    print("=" * 70)

if __name__ == '__main__':
    simulate_feedback_cycles()
