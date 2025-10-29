"""
Manually test saving feedback to database
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'projetPython.settings')
django.setup()

from users.models import CustomUser
from reco.models import Recommendation
from django.utils import timezone

def test_feedback_save():
    user = CustomUser.objects.get(username='hamouda')
    
    # Get a recommendation without feedback
    reco = Recommendation.objects.filter(user=user, feedback_at__isnull=True).first()
    
    if not reco:
        print("No recommendations without feedback found!")
        return
    
    print(f"Testing feedback save for recommendation ID {reco.id}")
    print(f"BEFORE: helpful={reco.helpful}, acted_upon={reco.acted_upon}, feedback_at={reco.feedback_at}")
    
    # Save feedback
    reco.helpful = True
    reco.acted_upon = True
    reco.feedback_at = timezone.now()
    reco.save()
    
    print(f"AFTER SAVE: helpful={reco.helpful}, acted_upon={reco.acted_upon}, feedback_at={reco.feedback_at}")
    
    # Reload from DB
    reco.refresh_from_db()
    print(f"AFTER RELOAD: helpful={reco.helpful}, acted_upon={reco.acted_upon}, feedback_at={reco.feedback_at}")
    
    # Check if it persisted
    check = Recommendation.objects.get(id=reco.id)
    print(f"FRESH QUERY: helpful={check.helpful}, acted_upon={check.acted_upon}, feedback_at={check.feedback_at}")
    
    if check.feedback_at:
        print("\n✅ SUCCESS! Feedback was saved to database!")
    else:
        print("\n❌ FAILED! Feedback did NOT save to database!")
    
    # Count total with feedback
    total_with_feedback = Recommendation.objects.filter(user=user, feedback_at__isnull=False).count()
    print(f"\nTotal recommendations with feedback for {user.username}: {total_with_feedback}")

if __name__ == '__main__':
    test_feedback_save()
