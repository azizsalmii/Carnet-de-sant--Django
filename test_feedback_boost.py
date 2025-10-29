"""
Test script to demonstrate how feedback increases confidence
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'projetPython.settings')
django.setup()

from users.models import CustomUser
from reco.models import Recommendation
from reco.services import generate_recommendations_for_user, compute_features_for_user
from django.utils import timezone
from django.db.models import Avg

def test_feedback_boost():
    user = CustomUser.objects.get(username='hamouda')
    
    print("=" * 60)
    print("CONFIDENCE BOOST TEST - Before and After Feedback")
    print("=" * 60)
    
    # Get current recommendations
    current_recos = Recommendation.objects.filter(user=user)
    
    print(f"\n📊 BEFORE FEEDBACK:")
    print(f"   Total recommendations: {current_recos.count()}")
    print(f"   With feedback: {current_recos.filter(feedback_at__isnull=False).count()}")
    print(f"   Average confidence: {current_recos.aggregate(avg=Avg('score'))['avg'] or 0:.2%}")
    
    # Give positive feedback to first 3 recommendations
    print(f"\n✅ GIVING POSITIVE FEEDBACK to 3 recommendations...")
    recos_to_feedback = current_recos[:3]
    
    for reco in recos_to_feedback:
        reco.helpful = True
        reco.acted_upon = True
        reco.feedback_at = timezone.now()
        reco.save()
        print(f"   ✓ {reco.category}: {reco.text[:60]}...")
    
    # Show updated stats
    print(f"\n📊 AFTER FEEDBACK (before regeneration):")
    current_recos = Recommendation.objects.filter(user=user)
    print(f"   With feedback: {current_recos.filter(feedback_at__isnull=False).count()}")
    print(f"   Marked helpful: {current_recos.filter(helpful=True).count()}")
    print(f"   Acted upon: {current_recos.filter(acted_upon=True).count()}")
    
    # Generate new recommendations with feedback learning
    print(f"\n🔄 GENERATING NEW RECOMMENDATIONS (with feedback learning)...")
    features = compute_features_for_user(user.id)
    new_count = generate_recommendations_for_user(user.id, features)
    
    # Show new confidence
    new_recos = Recommendation.objects.filter(user=user)
    new_avg_confidence = new_recos.aggregate(avg=Avg('score'))['avg'] or 0
    
    print(f"\n📊 AFTER REGENERATION:")
    print(f"   Total recommendations: {new_recos.count()}")
    print(f"   Average confidence: {new_avg_confidence:.2%}")
    print(f"   🚀 Confidence increased by: {(new_avg_confidence - 0.68) * 100:.1f} percentage points!")
    
    # Show top recommendations
    print(f"\n🏆 TOP 3 NEW RECOMMENDATIONS:")
    for reco in new_recos.order_by('-score')[:3]:
        print(f"   {reco.score:.1%} confidence - {reco.category}: {reco.text[:60]}...")
    
    print(f"\n" + "=" * 60)
    print("✅ TEST COMPLETE - Refresh your browser to see new recommendations!")
    print("=" * 60)

if __name__ == '__main__':
    test_feedback_boost()
