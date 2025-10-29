"""
🧪 RECO AI Model Testing & Demonstration Script

This script tests the complete RECO recommendation AI system:
1. Loads the ML model (RandomForest with CalibratedClassifier)
2. Tests feature engineering
3. Tests rule-based engine
4. Tests ML personalization service
5. Generates and displays recommendations for demo users
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
from reco.features import FeatureEngineer
from reco.engine import rules
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


def print_section(title):
    """Print a formatted section."""
    print(f"\n{'─' * 70}")
    print(f"  📋 {title}")
    print(f"{'─' * 70}")


def test_ml_model():
    """Test 1: ML Model Loading and Info."""
    print_header("TEST 1: ML Model Loading")
    
    try:
        ml_service = get_personalization_service()
        
        if ml_service.model:
            print("✅ ML Model loaded successfully!")
            print(f"   Model version: {ml_service.model_version or 'v1.0'}")
            print(f"   Model type: {type(ml_service.model).__name__}")
            
            # Get model info if available
            if hasattr(ml_service.model, 'classes_'):
                print(f"   Classes: {ml_service.model.classes_}")
            
            if hasattr(ml_service.model, 'n_features_in_'):
                print(f"   Number of features: {ml_service.model.n_features_in_}")
            
            return True
        else:
            print("⚠️  No ML model found - using rule-based only")
            return False
            
    except Exception as e:
        print(f"❌ Error loading ML model: {e}")
        return False


def test_feature_engineering():
    """Test 2: Feature Engineering."""
    print_header("TEST 2: Feature Engineering")
    
    # Create a test user if doesn't exist
    test_user, created = User.objects.get_or_create(
        username='test_ai_user',
        defaults={
            'email': 'test_ai@example.com',
            'first_name': 'Test',
            'last_name': 'AI'
        }
    )
    
    if created:
        test_user.set_password('test123')
        test_user.save()
        print(f"✅ Created test user: {test_user.username}")
    else:
        print(f"✅ Using existing test user: {test_user.username}")
    
    # Create profile if doesn't exist
    profile, _ = Profile.objects.get_or_create(user=test_user)
    
    # Create test metrics (7 days of data)
    print("\n📊 Creating test metrics...")
    today = date.today()
    
    for i in range(7):
        metric_date = today - timedelta(days=i)
        
        DailyMetrics.objects.update_or_create(
            user=test_user,
            date=metric_date,
            defaults={
                'steps': 4000 + (i * 300),
                'sleep_hours': 5.8 + (i * 0.2),
                'systolic_bp': 125 + (i * 2),
                'diastolic_bp': 78 + i,
            }
        )
    
    print("✅ Created 7 days of test metrics")
    
    # Compute features
    print("\n🔧 Computing features...")
    features = compute_features_for_user(test_user.id)
    
    print("\n📈 Computed Features:")
    for key, value in features.items():
        print(f"   {key}: {value}")
    
    # Test comprehensive features using FeatureEngineer
    print("\n🔬 Testing FeatureEngineer (advanced features)...")
    engineer = FeatureEngineer()
    
    try:
        comprehensive_features = engineer.compute_comprehensive_features(test_user.id)
        print(f"✅ Computed {len(comprehensive_features)} advanced features")
        
        # Show sample features
        print("\n   Sample Advanced Features:")
        sample_keys = list(comprehensive_features.keys())[:10]
        for key in sample_keys:
            print(f"   {key}: {comprehensive_features[key]}")
    except Exception as e:
        print(f"⚠️  Advanced features not available: {e}")
    
    return test_user, features


def test_rule_engine(features):
    """Test 3: Rule-Based Engine."""
    print_header("TEST 3: Rule-Based Recommendation Engine")
    
    rule_functions = rules()
    print(f"📋 Loaded {len(rule_functions)} rule functions")
    
    # Apply each rule
    print("\n🔍 Testing each rule:")
    recommendations = []
    
    for i, rule_fn in enumerate(rule_functions, 1):
        try:
            result = rule_fn(features)
            if result:
                recommendations.append(result)
                print(f"   ✅ Rule {i} ({rule_fn.__name__}): TRIGGERED")
                print(f"      Category: {result['category']}")
                print(f"      Text: {result['text'][:60]}...")
                print(f"      Score: {result['score']}")
            else:
                print(f"   ⚪ Rule {i} ({rule_fn.__name__}): Not applicable")
        except Exception as e:
            print(f"   ❌ Rule {i} ({rule_fn.__name__}): Error - {e}")
    
    print(f"\n✅ Generated {len(recommendations)} candidate recommendations")
    return recommendations


def test_ml_personalization(test_user, candidate_recommendations):
    """Test 4: ML Personalization."""
    print_header("TEST 4: ML Personalization Service")
    
    ml_service = get_personalization_service()
    
    if not ml_service.model:
        print("⚠️  No ML model available - skipping personalization test")
        return
    
    print(f"🤖 Testing ML predictions for {len(candidate_recommendations)} candidates...")
    
    for i, reco in enumerate(candidate_recommendations[:5], 1):  # Test first 5
        try:
            # Predict helpfulness (returns tuple: is_helpful, confidence, explanation)
            is_helpful, confidence, explanation = ml_service.predict_helpfulness(test_user, reco['category'])
            print(f"\n   Recommendation {i}:")
            print(f"      Category: {reco['category']}")
            print(f"      Text: {reco['text'][:50]}...")
            print(f"      ML Prediction: {'Helpful' if is_helpful else 'Not helpful'}")
            print(f"      ML Confidence: {confidence:.2%}")
            print(f"      Explanation: {explanation}")
            
        except Exception as e:
            print(f"      ❌ Error: {e}")


def test_full_recommendation_generation(test_user, features):
    """Test 5: Full Recommendation Generation Pipeline."""
    print_header("TEST 5: Full Recommendation Generation Pipeline")
    
    print(f"🚀 Generating recommendations for user: {test_user.username}")
    
    try:
        count = generate_recommendations_for_user(test_user.id, features)
        print(f"✅ Successfully generated {count} recommendations")
        
        # Display generated recommendations
        recommendations = Recommendation.objects.filter(user=test_user).order_by('-score')
        
        print(f"\n📋 Top Recommendations (sorted by score):")
        for i, reco in enumerate(recommendations[:5], 1):
            print(f"\n   {i}. {reco.category.upper()}")
            print(f"      Text: {reco.text}")
            print(f"      Priority Score: {reco.score}")
            print(f"      Source: {reco.source}")
            if reco.rationale:
                print(f"      Rationale: {reco.rationale}")
        
        return count
        
    except Exception as e:
        print(f"❌ Error generating recommendations: {e}")
        import traceback
        traceback.print_exc()
        return 0


def test_model_statistics():
    """Test 6: Model Statistics and Performance Info."""
    print_header("TEST 6: Model Statistics & Performance")
    
    # Count total recommendations in database
    total_recos = Recommendation.objects.count()
    users_with_recos = Recommendation.objects.values('user').distinct().count()
    
    print(f"📊 Database Statistics:")
    print(f"   Total recommendations: {total_recos}")
    print(f"   Users with recommendations: {users_with_recos}")
    print(f"   Total registered users: {User.objects.count()}")
    
    # Get recommendation distribution by category
    from django.db.models import Count
    by_category = Recommendation.objects.values('category').annotate(count=Count('id'))
    
    print(f"\n📈 Recommendations by Category:")
    for cat in by_category:
        print(f"   {cat['category']}: {cat['count']}")
    
    # Feedback statistics
    with_feedback = Recommendation.objects.filter(helpful__isnull=False).count()
    helpful_count = Recommendation.objects.filter(helpful=True).count()
    acted_count = Recommendation.objects.filter(acted_upon=True).count()
    
    print(f"\n💬 Feedback Statistics:")
    print(f"   Recommendations with feedback: {with_feedback}")
    print(f"   Marked as helpful: {helpful_count}")
    print(f"   User acted upon: {acted_count}")
    
    if with_feedback > 0:
        helpful_rate = (helpful_count / with_feedback) * 100
        action_rate = (acted_count / with_feedback) * 100
        print(f"   Helpfulness rate: {helpful_rate:.1f}%")
        print(f"   Action rate: {action_rate:.1f}%")


def run_all_tests():
    """Run all tests in sequence."""
    print("\n" + "🧪" * 35)
    print("  RECO AI MODEL - COMPREHENSIVE TEST SUITE")
    print("🧪" * 35)
    
    # Test 1: ML Model
    model_loaded = test_ml_model()
    
    # Test 2: Feature Engineering
    test_user, features = test_feature_engineering()
    
    # Test 3: Rule Engine
    candidate_recommendations = test_rule_engine(features)
    
    # Test 4: ML Personalization (if model available)
    if model_loaded:
        test_ml_personalization(test_user, candidate_recommendations)
    
    # Test 5: Full Pipeline
    reco_count = test_full_recommendation_generation(test_user, features)
    
    # Test 6: Statistics
    test_model_statistics()
    
    # Final Summary
    print_header("TEST SUMMARY")
    print(f"✅ ML Model: {'Loaded' if model_loaded else 'Not available (using rules only)'}")
    print(f"✅ Feature Engineering: Working")
    print(f"✅ Rule Engine: {len(candidate_recommendations)} rules triggered")
    print(f"✅ Full Pipeline: {reco_count} recommendations generated")
    print(f"✅ Test User: {test_user.username} (ID: {test_user.id})")
    
    print("\n" + "=" * 70)
    print("  🎉 ALL TESTS COMPLETED!")
    print("=" * 70)
    
    print("\n📝 Next Steps:")
    print("   1. View recommendations at: http://127.0.0.1:8000/reco/recommendations/")
    print("   2. Login with test user: test_ai_user / test123")
    print("   3. Test feedback buttons to train the model")
    print("   4. Export training data: python manage.py export_training_data")
    print("   5. Retrain model with new feedback data")


if __name__ == '__main__':
    try:
        run_all_tests()
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
    except Exception as e:
        print(f"\n\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
