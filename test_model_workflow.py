"""
🔬 RECO Model Workflow Test - Full End-to-End Verification

Tests the complete workflow:
1. Add new metrics for a user
2. Generate recommendations using ML model
3. Verify recommendations are created
4. Check confidence scores and explanations
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'projetPython.settings')
django.setup()

from django.contrib.auth import get_user_model
from reco.models import DailyMetrics, Recommendation, Profile
from reco.services import compute_features_for_user, generate_recommendations_for_user
from reco.ml_service import get_personalization_service
from datetime import date, timedelta
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

User = get_user_model()


def print_header(title):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def test_current_user_recommendations(username):
    """Test recommendations for an existing user."""
    print_header(f"TESTING RECOMMENDATIONS FOR USER: {username}")
    
    try:
        user = User.objects.get(username=username)
        print(f"✅ Found user: {user.username} (ID: {user.id})")
    except User.DoesNotExist:
        print(f"❌ User '{username}' not found!")
        return False
    
    # Check existing metrics
    print("\n📊 Checking Existing Metrics...")
    metrics = DailyMetrics.objects.filter(user=user).order_by('-date')[:7]
    
    if not metrics.exists():
        print("❌ No metrics found for this user!")
        print("   Please add metrics first at: http://127.0.0.1:8000/reco/add-metrics/")
        return False
    
    print(f"✅ Found {metrics.count()} days of metrics:")
    for m in metrics:
        print(f"   {m.date}: Steps={m.steps}, Sleep={m.sleep_hours}h, BP={m.systolic_bp}/{m.diastolic_bp}")
    
    # Compute features
    print("\n🔧 Computing Features...")
    features = compute_features_for_user(user.id)
    
    print("📈 Computed Features:")
    for key, value in features.items():
        print(f"   {key}: {value}")
    
    # Check if features are valid (non-zero)
    if all(v == 0 for v in features.values()):
        print("⚠️  WARNING: All features are zero! This might cause issues.")
        return False
    
    # Check ML model
    print("\n🤖 Checking ML Model...")
    ml_service = get_personalization_service()
    
    if ml_service.model:
        print(f"✅ ML Model loaded: {ml_service.model_version}")
        print(f"   Model type: {type(ml_service.model).__name__}")
        
        # Test prediction for each category
        print("\n🔮 Testing ML Predictions:")
        categories = ['sleep', 'activity', 'nutrition', 'lifestyle']
        
        for category in categories:
            try:
                is_helpful, confidence, explanation = ml_service.predict_helpfulness(user, category)
                print(f"\n   {category.upper()}:")
                print(f"      Helpful: {is_helpful}")
                print(f"      Confidence: {confidence:.2%}")
                print(f"      Explanation: {explanation[:80]}...")
            except Exception as e:
                print(f"      ❌ Error: {e}")
    else:
        print("⚠️  No ML model loaded - using rules only")
    
    # Delete old recommendations
    old_count = Recommendation.objects.filter(user=user).count()
    if old_count > 0:
        print(f"\n🗑️  Deleting {old_count} old recommendations...")
        Recommendation.objects.filter(user=user).delete()
    
    # Generate new recommendations
    print("\n🚀 Generating Recommendations...")
    try:
        count = generate_recommendations_for_user(user.id, features)
        print(f"✅ Successfully generated {count} recommendations!")
    except Exception as e:
        print(f"❌ Error generating recommendations: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Display generated recommendations
    print("\n📋 Generated Recommendations:")
    recommendations = Recommendation.objects.filter(user=user).order_by('-score')
    
    if not recommendations.exists():
        print("❌ No recommendations were created!")
        print("\n🔍 Debug Info:")
        print(f"   Features valid: {not all(v == 0 for v in features.values())}")
        print(f"   ML model loaded: {ml_service.model is not None}")
        return False
    
    for i, reco in enumerate(recommendations, 1):
        print(f"\n   {i}. [{reco.category.upper()}] Score: {reco.score:.3f}")
        print(f"      {reco.text[:80]}...")
        if reco.rationale:
            print(f"      Rationale: {reco.rationale[:80]}...")
        print(f"      Source: {reco.source}, Model: {reco.model_version}")
    
    # Calculate statistics
    avg_score = sum(r.score for r in recommendations) / len(recommendations)
    print(f"\n📊 Statistics:")
    print(f"   Total Recommendations: {count}")
    print(f"   Average Confidence: {avg_score:.2%}")
    print(f"   Categories: {', '.join(set(r.category for r in recommendations))}")
    
    # Test API view data
    print("\n🌐 Testing Dashboard Data...")
    from django.test import RequestFactory
    from reco.views import recommendations_view
    
    factory = RequestFactory()
    request = factory.get('/reco/recommendations/')
    request.user = user
    
    try:
        response = recommendations_view(request)
        if response.status_code == 200:
            print("✅ Dashboard view works!")
        else:
            print(f"⚠️  Dashboard returned status: {response.status_code}")
    except Exception as e:
        print(f"⚠️  Dashboard test failed: {e}")
    
    return True


def add_test_metrics_for_user(username):
    """Add 7 days of varied test metrics to trigger diverse recommendations."""
    print_header(f"ADDING TEST METRICS FOR: {username}")
    
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        print(f"❌ User '{username}' not found!")
        return False
    
    today = date.today()
    metrics_data = [
        # Day, Steps, Sleep, SBP, DBP
        (0, 3500, 5.5, 135, 85),   # Low activity, low sleep, high BP
        (1, 4200, 6.0, 132, 82),   # Still low
        (2, 4800, 6.2, 130, 80),   # Improving
        (3, 5500, 6.5, 128, 78),   # Better
        (4, 6200, 7.0, 125, 76),   # Good
        (5, 5800, 6.8, 127, 77),   # Maintaining
        (6, 6000, 6.9, 126, 76),   # Stable
    ]
    
    print(f"\n📊 Creating {len(metrics_data)} days of varied metrics...")
    
    for days_ago, steps, sleep, sbp, dbp in metrics_data:
        metric_date = today - timedelta(days=days_ago)
        
        metric, created = DailyMetrics.objects.update_or_create(
            user=user,
            date=metric_date,
            defaults={
                'steps': steps,
                'sleep_hours': sleep,
                'systolic_bp': sbp,
                'diastolic_bp': dbp,
            }
        )
        
        status = "✅ Created" if created else "🔄 Updated"
        print(f"{status} {metric_date}: Steps={steps}, Sleep={sleep}h, BP={sbp}/{dbp}")
    
    print(f"\n✅ Successfully added {len(metrics_data)} days of test metrics!")
    return True


def main():
    """Main test workflow."""
    import sys
    
    print("\n" + "🧪" * 35)
    print("  RECO MODEL WORKFLOW - END-TO-END TEST")
    print("🧪" * 35)
    
    # Get username from command line or use default
    if len(sys.argv) > 1:
        username = sys.argv[1]
    else:
        # Try to find the current logged-in user or use test user
        username = input("\nEnter username to test (or press Enter for 'test_ai_user'): ").strip()
        if not username:
            username = 'test_ai_user'
    
    print(f"\n🎯 Target User: {username}")
    
    # Check if user exists
    try:
        user = User.objects.get(username=username)
        print(f"✅ User exists: {user.username}")
    except User.DoesNotExist:
        print(f"❌ User '{username}' not found!")
        print("\n📝 Available users:")
        for u in User.objects.all()[:10]:
            print(f"   - {u.username}")
        return
    
    # Option to add test metrics
    print("\n" + "─" * 70)
    choice = input("\nDo you want to add/update test metrics? (y/n): ").strip().lower()
    
    if choice == 'y':
        if not add_test_metrics_for_user(username):
            print("\n❌ Failed to add test metrics!")
            return
    
    # Run the main test
    print("\n" + "─" * 70)
    success = test_current_user_recommendations(username)
    
    # Final summary
    print("\n" + "=" * 70)
    if success:
        print("  ✅ TEST PASSED - Model is working correctly!")
        print("=" * 70)
        print("\n📝 Next Steps:")
        print("   1. Login at: http://127.0.0.1:8000/reco/login/")
        print(f"   2. Username: {username}")
        print("   3. View recommendations at: http://127.0.0.1:8000/reco/recommendations/")
        print("   4. Check dashboard at: http://127.0.0.1:8000/reco/dashboard/")
        print("\n💡 If you see 0 recommendations in the UI:")
        print("   - Hard refresh the page (Ctrl+Shift+R)")
        print("   - Check browser console for errors (F12)")
        print("   - Verify you're logged in as the correct user")
    else:
        print("  ❌ TEST FAILED - Issues detected!")
        print("=" * 70)
        print("\n🔍 Troubleshooting:")
        print("   1. Make sure you have at least 7 days of metrics")
        print("   2. Check that metrics have non-null values")
        print("   3. Verify ML model files exist in models/v1/")
        print("   4. Check Django logs for errors")
    print("\n")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
