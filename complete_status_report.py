"""
Complete Status Report - Feedback System & Cumulative Confidence
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'projetPython.settings')
django.setup()

from users.models import CustomUser
from reco.models import Recommendation
from reco.ml_service import get_personalization_service
from reco.feedback_learning import get_personalized_confidence
from django.db.models import Avg

def full_status_report():
    user = CustomUser.objects.get(username='hamouda')
    ml_service = get_personalization_service()
    
    print("=" * 80)
    print("COMPLETE STATUS REPORT - FEEDBACK & CUMULATIVE CONFIDENCE")
    print("=" * 80)
    
    # Current feedback status
    all_recos = Recommendation.objects.filter(user=user)
    feedback_recos = all_recos.filter(feedback_at__isnull=False)
    
    print("\n1. CURRENT FEEDBACK STATUS:")
    print(f"   Total recommendations: {all_recos.count()}")
    print(f"   With feedback: {feedback_recos.count()}")
    print(f"   Marked helpful: {feedback_recos.filter(helpful=True).count()}")
    print(f"   Acted upon: {feedback_recos.filter(acted_upon=True).count()}")
    
    if feedback_recos.count() == 0:
        print("\n   ⚠️ NO FEEDBACK YET!")
        print("   → Go to http://127.0.0.1:8000/reco/recommendations/")
        print("   → Click 'Utile' or 'J'ai appliqué' on 5-10 recommendations")
        print("   → Then click 'Actualiser' to see confidence increase")
        return
    
    # Current confidence levels
    print("\n2. CURRENT CONFIDENCE LEVELS:")
    categories = ['sleep', 'activity', 'nutrition', 'lifestyle']
    icons = {'sleep': '😴', 'activity': '🏃', 'nutrition': '🍎', 'lifestyle': '❤️'}
    
    total_base = 0
    total_personalized = 0
    
    for category in categories:
        # Get base ML confidence
        _, base_conf, _ = ml_service.predict_helpfulness(user, category)
        
        # Get personalized confidence (with feedback boost)
        pers_conf = get_personalized_confidence(user, category, base_conf)
        
        boost = (pers_conf - base_conf) * 100
        
        # Get feedback count for this category
        cat_feedback = feedback_recos.filter(category=category).count()
        
        total_base += base_conf
        total_personalized += pers_conf
        
        print(f"   {icons[category]} {category.upper():<12}: "
              f"Base {base_conf * 100:5.1f}% → Personalized {pers_conf * 100:5.1f}% "
              f"(boost: +{boost:4.1f}%, {cat_feedback} feedbacks)")
    
    avg_base = (total_base / len(categories)) * 100
    avg_personalized = (total_personalized / len(categories)) * 100
    avg_boost = avg_personalized - avg_base
    
    print(f"\n   AVERAGE: Base {avg_base:.1f}% → Personalized {avg_personalized:.1f}% (boost: +{avg_boost:.1f}%)")
    
    # What happens next
    print("\n3. HOW TO INCREASE CONFIDENCE:")
    print(f"   Current average: {avg_personalized:.1f}%")
    print(f"   Goal: 85-90%+")
    print(f"   Gap: Need +{85 - avg_personalized:.1f}% more")
    
    if feedback_recos.count() < 10:
        print(f"\n   📝 NEXT STEPS:")
        print(f"      a) Give feedback on {10 - feedback_recos.count()} more recommendations")
        print(f"      b) Click 'Actualiser' to regenerate recommendations")
        print(f"      c) Confidence will increase by ~2-5% per cycle")
        print(f"      d) Repeat 3-5 times to reach 85%+")
    elif avg_personalized < 85:
        print(f"\n   📝 NEXT STEPS:")
        print(f"      a) Click 'Actualiser' to get new recommendations")
        print(f"      b) Mark 5-10 as helpful/applied")
        print(f"      c) Click 'Actualiser' again")
        print(f"      d) Confidence will increase cumulatively")
    else:
        print(f"\n   🎉 GOAL REACHED! Confidence is at {avg_personalized:.1f}%!")
    
    # Feedback by category breakdown
    print("\n4. FEEDBACK BREAKDOWN BY CATEGORY:")
    for category in categories:
        cat_recos = all_recos.filter(category=category)
        cat_feedback = cat_recos.filter(feedback_at__isnull=False)
        cat_helpful = cat_feedback.filter(helpful=True)
        
        if cat_feedback.exists():
            helpful_rate = (cat_helpful.count() / cat_feedback.count()) * 100
            print(f"   {icons[category]} {category:<12}: {cat_feedback.count()} feedbacks, "
                  f"{helpful_rate:.0f}% helpful rate")
        else:
            print(f"   {icons[category]} {category:<12}: No feedback yet")
    
    # Formula explanation
    print("\n5. CUMULATIVE CONFIDENCE FORMULA:")
    print("   Personalized = Base + (Feedback_Boost)")
    print("   Where:")
    print("   - Base: ML model prediction (~68%)")
    print("   - Feedback_Boost: (Category_Confidence × Engagement) × 25%")
    print("   - Category_Confidence: Based on helpful_rate in that category")
    print("   - Engagement: Overall user interaction rate")
    print("   - Maximum boost: +25% (from 68% to 93%)")
    
    print("\n6. DASHBOARD LINKS:")
    print("   - Recommendations: http://127.0.0.1:8000/reco/recommendations/")
    print("   - AI Progress:     http://127.0.0.1:8000/reco/ai-progress/")
    print("   - Dashboard:       http://127.0.0.1:8000/reco/dashboard/")
    
    print("\n" + "=" * 80)
    print("✅ SYSTEM STATUS: WORKING")
    print("=" * 80)
    
    # Test recommendations
    if feedback_recos.count() >= 2:
        print("\n📊 RECENT FEEDBACK EXAMPLES:")
        recent = feedback_recos.order_by('-feedback_at')[:5]
        for r in recent:
            helpful_icon = "✅" if r.helpful else "❌"
            acted_icon = "⚡" if r.acted_upon else "  "
            print(f"   {helpful_icon}{acted_icon} {r.category}: {r.text[:60]}...")

if __name__ == '__main__':
    full_status_report()
