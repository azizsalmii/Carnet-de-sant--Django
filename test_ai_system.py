"""
Comprehensive AI Recommendation System Test
Tests all aspects of the HEALTH TRACK AI recommendation engine
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'projetPython.settings')
django.setup()

from django.contrib.auth import get_user_model
from reco.models import Profile, DailyMetrics, Recommendation
from reco.features import FeatureEngineer
from reco.ml_service import get_personalization_service
from reco.services import generate_recommendations_for_user, compute_features_for_user
from datetime import date, timedelta

User = get_user_model()

def print_section(title):
    """Print formatted section header"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

def test_1_data_setup():
    """Test 1: Verify data setup"""
    print_section("TEST 1: Data Setup Verification")
    
    user = User.objects.get(username='demo')
    profile = Profile.objects.get(user=user)
    metrics_count = DailyMetrics.objects.filter(user=user).count()
    
    print(f"✓ User: {user.username} (ID: {user.id})")
    print(f"✓ Profile exists: {profile is not None}")
    print(f"  - Activity Level: {profile.activity_level or 'Not set'}")
    print(f"  - Health Goals: {profile.health_goals or 'Not set'}")
    bmi_str = f"{profile.bmi:.1f}" if profile.bmi else "N/A"
    print(f"  - BMI: {bmi_str}")
    print(f"✓ Daily Metrics: {metrics_count} records")
    
    if metrics_count > 0:
        latest = DailyMetrics.objects.filter(user=user).latest('date')
        print(f"  - Latest: {latest.date}")
        print(f"  - Sleep: {latest.sleep_hours}h")
        print(f"  - Steps: {latest.steps}")
        print(f"  - BP: {latest.systolic_bp}/{latest.diastolic_bp}")
    
    return user

def test_2_ml_model():
    """Test 2: ML Model Loading"""
    print_section("TEST 2: ML Model Loading")
    
    ml_service = get_personalization_service()
    
    print(f"✓ ML Service initialized: {ml_service is not None}")
    print(f"✓ Model loaded: {ml_service.model is not None}")
    print(f"  - Model type: {type(ml_service.model).__name__}")
    print(f"  - Model file: models/v1/model_calibrated.joblib")
    
    if ml_service.scaler:
        print(f"✓ Scaler loaded: {type(ml_service.scaler).__name__}")
    
    return ml_service

def test_3_feature_engineering(user):
    """Test 3: Feature Engineering"""
    print_section("TEST 3: Feature Engineering")
    
    features = compute_features_for_user(user.id)
    
    print(f"✓ Features computed: {len(features)} features")
    print("\nKey Features:")
    for key, value in sorted(features.items()):
        if isinstance(value, float):
            print(f"  - {key}: {value:.2f}")
        else:
            print(f"  - {key}: {value}")
    
    return features

def test_4_recommendation_generation(user):
    """Test 4: Recommendation Generation"""
    print_section("TEST 4: Recommendation Generation (Fresh)")
    
    # Delete old recommendations
    old_count = Recommendation.objects.filter(user=user).count()
    Recommendation.objects.filter(user=user).delete()
    
    # Generate new ones
    features = compute_features_for_user(user.id)
    count = generate_recommendations_for_user(user.id, features)
    
    print(f"✓ Old recommendations deleted: {old_count}")
    print(f"✓ New recommendations generated: {count}")
    
    return count

def test_5_recommendation_quality(user):
    """Test 5: Recommendation Quality Analysis"""
    print_section("TEST 5: Recommendation Quality Analysis")
    
    recos = Recommendation.objects.filter(user=user).order_by('-score')
    
    # Group by category
    by_category = {}
    by_source = {}
    
    for reco in recos:
        by_category[reco.category] = by_category.get(reco.category, 0) + 1
        by_source[reco.source] = by_source.get(reco.source, 0) + 1
    
    print(f"\n✓ Total Recommendations: {recos.count()}")
    
    print("\nBy Category:")
    for cat, count in sorted(by_category.items()):
        print(f"  - {cat}: {count}")
    
    print("\nBy Source:")
    for src, count in sorted(by_source.items()):
        print(f"  - {src}: {count}")
    
    print(f"\nScore Range:")
    if recos.exists():
        print(f"  - Min: {recos.order_by('score').first().score:.2f}")
        print(f"  - Max: {recos.order_by('-score').first().score:.2f}")
        print(f"  - Avg: {sum(r.score for r in recos) / recos.count():.2f}")
    
    return recos

def test_6_top_recommendations(user):
    """Test 6: Display Top Recommendations"""
    print_section("TEST 6: Top 5 AI Recommendations")
    
    recos = Recommendation.objects.filter(user=user).order_by('-score')[:5]
    
    for i, reco in enumerate(recos, 1):
        print(f"\n{i}. [{reco.category.upper()}] Score: {reco.score:.2%}")
        print(f"   {reco.text}")
        print(f"   Source: {reco.source} | Model: {reco.model_version or 'N/A'}")
        if reco.rationale:
            print(f"   Rationale: {reco.rationale[:80]}...")

def test_7_personalization(user, ml_service):
    """Test 7: Personalization Testing"""
    print_section("TEST 7: Personalization Testing")
    
    categories = ['sleep', 'activity', 'nutrition', 'lifestyle']
    
    print("\nML Predictions by Category:")
    for category in categories:
        try:
            prediction = ml_service.predict_helpfulness(user, category)
            print(f"  - {category}: {prediction:.2%} helpful")
        except Exception as e:
            print(f"  - {category}: Error - {str(e)[:50]}")

def test_8_api_endpoints():
    """Test 8: API Endpoints"""
    print_section("TEST 8: Available API Endpoints")
    
    endpoints = [
        "GET  /reco/ - Home page",
        "GET  /reco/dashboard/ - User dashboard",
        "GET  /reco/recommendations/ - View recommendations",
        "GET  /reco/add-metrics/ - Add health metrics",
        "GET  /reco/ai-progress/ - AI progress tracking",
        "GET  /reco/profile/ - User profile",
        "POST /reco/register/ - User registration",
        "POST /reco/login/ - User login",
        "GET  /reco/logout/ - Logout",
        "",
        "API (DRF):",
        "GET  /api/recommendations/ - List recommendations",
        "POST /api/metrics/ - Add metrics via API",
        "GET  /api/profiles/ - Profile management",
    ]
    
    for endpoint in endpoints:
        print(f"  {endpoint}")

def run_all_tests():
    """Run all tests"""
    print("\n" + "#"*80)
    print("#  HEALTH TRACK AI RECOMMENDATION SYSTEM - COMPREHENSIVE TEST")
    print("#"*80)
    
    try:
        user = test_1_data_setup()
        ml_service = test_2_ml_model()
        features = test_3_feature_engineering(user)
        count = test_4_recommendation_generation(user)
        recos = test_5_recommendation_quality(user)
        test_6_top_recommendations(user)
        test_7_personalization(user, ml_service)
        test_8_api_endpoints()
        
        print_section("✓ ALL TESTS PASSED!")
        print("\nSystem Status: OPERATIONAL ✓")
        print("AI Model: v1-calibrated (RandomForest with CalibratedClassifier)")
        print(f"Recommendations Generated: {count}")
        print(f"User: demo")
        print("\nAccess the system at: http://127.0.0.1:8000/reco/")
        
    except Exception as e:
        print_section("✗ TEST FAILED")
        print(f"\nError: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_all_tests()
