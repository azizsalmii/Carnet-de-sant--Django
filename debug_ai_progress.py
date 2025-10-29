"""
Debug AI Progress Page - Check why feedback count is 0
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'projetPython.settings')
django.setup()

from users.models import CustomUser
from reco.models import Recommendation
from reco.feedback_learning import get_feedback_insights

def debug_ai_progress():
    user = CustomUser.objects.get(username='hamouda')
    
    print("=" * 70)
    print("DEBUG: AI PROGRESS PAGE - FEEDBACK COUNT ISSUE")
    print("=" * 70)
    
    # Direct database query
    print("\n1. DIRECT DATABASE QUERIES:")
    all_recos = Recommendation.objects.filter(user=user)
    print(f"   Total recommendations: {all_recos.count()}")
    
    feedback_recos = all_recos.filter(feedback_at__isnull=False)
    print(f"   With feedback_at NOT NULL: {feedback_recos.count()}")
    
    helpful_recos = all_recos.filter(helpful=True)
    print(f"   With helpful=True: {helpful_recos.count()}")
    
    acted_recos = all_recos.filter(acted_upon=True)
    print(f"   With acted_upon=True: {acted_recos.count()}")
    
    # Show some examples
    if feedback_recos.exists():
        print(f"\n   EXAMPLES WITH feedback_at:")
        for r in feedback_recos[:3]:
            print(f"      ID {r.id}: helpful={r.helpful}, acted={r.acted_upon}, time={r.feedback_at}")
    
    # Test get_feedback_insights function
    print(f"\n2. get_feedback_insights() FUNCTION:")
    insights = get_feedback_insights(user)
    print(f"   total_feedback: {insights['total_feedback']}")
    print(f"   helpful_rate: {insights['helpful_rate']:.1f}%")
    print(f"   action_rate: {insights['action_rate']:.1f}%")
    print(f"   favorite_category: {insights.get('favorite_category')}")
    print(f"   learning_status: {insights.get('learning_status')}")
    
    # Check what the view would pass to template
    print(f"\n3. WHAT THE VIEW PASSES TO TEMPLATE:")
    print(f"   context['total_feedback'] = {insights['total_feedback']}")
    print(f"   context['helpful_rate'] = {insights['helpful_rate']}")
    
    # Check if the issue is feedback_at being NULL
    print(f"\n4. CHECKING feedback_at VALUES:")
    null_feedback_at = all_recos.filter(feedback_at__isnull=True)
    print(f"   Recommendations with NULL feedback_at: {null_feedback_at.count()}")
    
    not_null_feedback_at = all_recos.filter(feedback_at__isnull=False)
    print(f"   Recommendations with NOT NULL feedback_at: {not_null_feedback_at.count()}")
    
    # Check if helpful/acted_upon are set WITHOUT feedback_at
    orphaned = all_recos.filter(helpful=True, feedback_at__isnull=True)
    print(f"\n5. ORPHANED FEEDBACK (helpful=True but feedback_at=NULL):")
    print(f"   Count: {orphaned.count()}")
    
    if orphaned.exists():
        print(f"   ⚠️ PROBLEM FOUND: Feedback was marked but feedback_at was not set!")
        print(f"   These recommendations:")
        for r in orphaned[:5]:
            print(f"      ID {r.id}: {r.category} - {r.text[:50]}...")
        
        print(f"\n   🔧 FIXING: Setting feedback_at for orphaned feedback...")
        from django.utils import timezone
        count = 0
        for r in orphaned:
            r.feedback_at = timezone.now()
            r.save()
            count += 1
        print(f"   ✅ Fixed {count} recommendations!")
        
        # Re-test
        print(f"\n6. AFTER FIX:")
        insights_after = get_feedback_insights(user)
        print(f"   total_feedback: {insights_after['total_feedback']}")
        print(f"   helpful_rate: {insights_after['helpful_rate']:.1f}%")
    else:
        print(f"   ✅ No orphaned feedback found")
    
    print("\n" + "=" * 70)
    print("Refresh http://127.0.0.1:8000/reco/ai-progress/ to see updated data")
    print("=" * 70)

if __name__ == '__main__':
    debug_ai_progress()
