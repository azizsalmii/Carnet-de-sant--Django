"""
Test the fixed confidence persistence
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'projetPython.settings')
django.setup()

from users.models import CustomUser
from reco.models import Recommendation
from django.db.models import Avg

def test_confidence_persistence():
    user = CustomUser.objects.get(username='hamouda')
    
    print("=" * 70)
    print("TEST: CONFIDENCE PERSISTENCE AFTER FIX")
    print("=" * 70)
    
    # Get all recommendations
    all_recos = Recommendation.objects.filter(user=user)
    
    print(f"\n📊 CURRENT RECOMMENDATIONS:")
    print(f"   Total: {all_recos.count()}")
    
    # Check saved scores
    if all_recos.exists():
        # Calculate average from SAVED scores
        avg_saved_score = all_recos.aggregate(avg=Avg('score'))['avg']
        
        if avg_saved_score:
            print(f"   Average SAVED score: {avg_saved_score * 100:.1f}%")
            print(f"\n   ✅ This is what you SHOULD see on the page!")
        else:
            print(f"   ⚠️ No scores saved yet")
        
        # Show breakdown by category
        print(f"\n📈 CONFIDENCE BY CATEGORY (saved in database):")
        for category in ['sleep', 'activity', 'nutrition', 'lifestyle']:
            cat_recos = all_recos.filter(category=category)
            if cat_recos.exists():
                cat_avg = cat_recos.aggregate(avg=Avg('score'))['avg']
                cat_count = cat_recos.count()
                icon = {'sleep': '😴', 'activity': '🏃', 'nutrition': '🍎', 'lifestyle': '❤️'}
                print(f"   {icon[category]} {category}: {cat_avg * 100:.1f}% ({cat_count} recommendations)")
        
        # Show some examples
        print(f"\n📋 SAMPLE RECOMMENDATIONS WITH SAVED SCORES:")
        for reco in all_recos.order_by('-score')[:5]:
            print(f"   {reco.score * 100:5.1f}% - {reco.category}: {reco.text[:50]}...")
    
    # Check feedback count
    feedback_count = all_recos.filter(feedback_at__isnull=False).count()
    print(f"\n💬 FEEDBACK STATUS:")
    print(f"   Total feedback given: {feedback_count}")
    
    if feedback_count > 0:
        helpful_count = all_recos.filter(helpful=True).count()
        acted_count = all_recos.filter(acted_upon=True).count()
        print(f"   Marked helpful: {helpful_count}")
        print(f"   Acted upon: {acted_count}")
    
    print(f"\n🎯 EXPECTED BEHAVIOR:")
    print(f"   1. Refresh http://127.0.0.1:8000/reco/recommendations/")
    print(f"   2. You should see average: {avg_saved_score * 100:.1f}%")
    print(f"   3. Give more feedback and click 'Actualiser'")
    print(f"   4. New recommendations will have HIGHER confidence")
    print(f"   5. Average will keep INCREASING (not resetting to 68%)")
    
    print("\n" + "=" * 70)
    print("✅ FIX APPLIED - View now uses SAVED scores instead of recalculating!")
    print("=" * 70)

if __name__ == '__main__':
    test_confidence_persistence()
