"""
Check current feedback statistics for the dashboard
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'projetPython.settings')
django.setup()

from users.models import CustomUser
from reco.models import Recommendation
from django.db.models import Avg, Count

def check_feedback_stats():
    user = CustomUser.objects.get(username='hamouda')
    
    print("=" * 60)
    print("CURRENT FEEDBACK STATISTICS FOR AI PROGRESS DASHBOARD")
    print("=" * 60)
    
    # Get all recommendations
    all_recos = Recommendation.objects.filter(user=user)
    feedback_recos = all_recos.filter(feedback_at__isnull=False)
    helpful_recos = all_recos.filter(helpful=True)
    acted_recos = all_recos.filter(acted_upon=True)
    
    print(f"\n📊 OVERALL STATS:")
    print(f"   Total recommendations: {all_recos.count()}")
    print(f"   With feedback: {feedback_recos.count()}")
    print(f"   Marked helpful: {helpful_recos.count()}")
    print(f"   Acted upon: {acted_recos.count()}")
    
    if feedback_recos.exists():
        helpful_rate = (helpful_recos.count() / feedback_recos.count()) * 100
        print(f"   Helpful rate: {helpful_rate:.1f}%")
    
    # Average confidence
    avg_conf = all_recos.aggregate(avg=Avg('score'))['avg']
    if avg_conf:
        print(f"   Average confidence: {avg_conf * 100:.1f}%")
    
    # Stats by category
    print(f"\n📈 STATS BY CATEGORY:")
    categories = ['sleep', 'activity', 'nutrition', 'lifestyle']
    
    for category in categories:
        cat_recos = all_recos.filter(category=category)
        cat_feedback = cat_recos.filter(feedback_at__isnull=False)
        cat_helpful = cat_recos.filter(helpful=True)
        
        icon = {
            'sleep': '😴',
            'activity': '🏃',
            'nutrition': '🍎',
            'lifestyle': '❤️'
        }
        
        print(f"\n   {icon[category]} {category.upper()}:")
        print(f"      Total: {cat_recos.count()}")
        print(f"      With feedback: {cat_feedback.count()}")
        print(f"      Marked helpful: {cat_helpful.count()}")
        
        if cat_feedback.exists():
            helpful_rate = (cat_helpful.count() / cat_feedback.count()) * 100
            print(f"      Helpful rate: {helpful_rate:.1f}%")
        
        avg_cat_conf = cat_recos.aggregate(avg=Avg('score'))['avg']
        if avg_cat_conf:
            print(f"      Avg confidence: {avg_cat_conf * 100:.1f}%")
    
    # Recent feedback examples
    print(f"\n📝 RECENT FEEDBACK (last 10):")
    recent = feedback_recos.order_by('-feedback_at')[:10]
    for r in recent:
        helpful_icon = "✅" if r.helpful else "❌"
        acted_icon = "⚡" if r.acted_upon else "  "
        print(f"   {helpful_icon}{acted_icon} {r.category}: {r.text[:50]}...")
    
    print(f"\n" + "=" * 60)
    print("✅ Check the dashboard at: http://127.0.0.1:8000/reco/ai-progress/")
    print("=" * 60)

if __name__ == '__main__':
    check_feedback_stats()
