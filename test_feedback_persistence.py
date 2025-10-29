"""
Test the feedback persistence fix
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'projetPython.settings')
django.setup()

from users.models import CustomUser
from reco.models import Recommendation
from reco.services import generate_recommendations_for_user, compute_features_for_user
from django.utils import timezone

def test_feedback_persistence():
    user = CustomUser.objects.get(username='hamouda')
    
    print("=" * 70)
    print("TEST: FEEDBACK PERSISTENCE AFTER ACTUALISER")
    print("=" * 70)
    
    # Step 1: Check current state
    print("\n1. CURRENT STATE:")
    all_recos = Recommendation.objects.filter(user=user)
    feedback_recos = all_recos.filter(feedback_at__isnull=False)
    print(f"   Total recommendations: {all_recos.count()}")
    print(f"   With feedback: {feedback_recos.count()}")
    
    # Step 2: Give feedback to some recommendations
    print("\n2. GIVING FEEDBACK TO 3 RECOMMENDATIONS:")
    recos_to_feedback = all_recos.filter(feedback_at__isnull=True)[:3]
    
    if recos_to_feedback.count() < 3:
        print("   Not enough recommendations without feedback!")
    else:
        for reco in recos_to_feedback:
            reco.helpful = True
            reco.acted_upon = False
            reco.feedback_at = timezone.now()
            reco.save()
            print(f"   ✅ Gave feedback to: {reco.category} - {reco.text[:40]}...")
    
    # Check after feedback
    feedback_after = Recommendation.objects.filter(user=user, feedback_at__isnull=False)
    print(f"\n   Total with feedback NOW: {feedback_after.count()}")
    
    # Step 3: Generate new recommendations (like clicking Actualiser)
    print("\n3. GENERATING NEW RECOMMENDATIONS (simulating Actualiser):")
    features = compute_features_for_user(user.id)
    new_count = generate_recommendations_for_user(user.id, features)
    print(f"   Generated {new_count} new recommendations")
    
    # Step 4: Check if feedback was preserved
    print("\n4. AFTER GENERATION - CHECKING FEEDBACK PRESERVATION:")
    all_recos_after = Recommendation.objects.filter(user=user)
    feedback_after_gen = all_recos_after.filter(feedback_at__isnull=False)
    
    print(f"   Total recommendations: {all_recos_after.count()}")
    print(f"   With feedback: {feedback_after_gen.count()}")
    
    if feedback_after_gen.count() >= feedback_after.count():
        print(f"\n   ✅ SUCCESS! Feedback was PRESERVED!")
        print(f"   Old feedback count: {feedback_after.count()}")
        print(f"   New feedback count: {feedback_after_gen.count()}")
        
        # Show preserved feedback
        print(f"\n   PRESERVED FEEDBACK EXAMPLES:")
        for r in feedback_after_gen[:5]:
            print(f"      {r.category}: helpful={r.helpful}, acted={r.acted_upon}")
    else:
        print(f"\n   ❌ FAILED! Feedback was DELETED!")
        print(f"   Lost {feedback_after.count() - feedback_after_gen.count()} feedbacks")
    
    # Step 5: Check AI progress page data
    from reco.feedback_learning import get_feedback_insights
    insights = get_feedback_insights(user)
    
    print(f"\n5. AI PROGRESS PAGE DATA:")
    print(f"   Total feedback: {insights['total_feedback']}")
    print(f"   Helpful rate: {insights['helpful_rate']:.1f}%")
    print(f"   Action rate: {insights['action_rate']:.1f}%")
    
    if insights['total_feedback'] > 0:
        print(f"\n   ✅ AI Progress page will now show feedback data!")
    else:
        print(f"\n   ❌ Still showing 0 feedbacks")
    
    print("\n" + "=" * 70)
    print("Refresh http://127.0.0.1:8000/reco/ai-progress/ to see the data!")
    print("=" * 70)

if __name__ == '__main__':
    test_feedback_persistence()
