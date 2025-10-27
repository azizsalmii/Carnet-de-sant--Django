"""
Tests for HEALTH TRACK recommendation system.
"""
from datetime import date, timedelta
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status

from .models import Profile, DailyMetrics, Recommendation
from .services import compute_features_for_user, generate_recommendations_for_user
from .engine import rules

User = get_user_model()


class ModelTests(TestCase):
    """Tests for models."""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
    
    def test_profile_creation(self):
        """Test creating a user profile."""
        profile = Profile.objects.create(
            user=self.user,
            sex='M',
            height_cm=175.0,
            weight_kg=70.0
        )
        self.assertEqual(str(profile), 'Profile: testuser')
    
    def test_daily_metrics_unique_constraint(self):
        """Test that user+date is unique for DailyMetrics."""
        today = date.today()
        DailyMetrics.objects.create(
            user=self.user,
            date=today,
            steps=5000,
            sleep_hours=7.0
        )
        
        # Try to create duplicate - should raise IntegrityError
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            DailyMetrics.objects.create(
                user=self.user,
                date=today,
                steps=6000,
                sleep_hours=8.0
            )
    
    def test_daily_metrics_str(self):
        """Test DailyMetrics string representation."""
        today = date.today()
        metrics = DailyMetrics.objects.create(
            user=self.user,
            date=today,
            steps=5000
        )
        self.assertEqual(str(metrics), f'testuser - {today}')
    
    def test_recommendation_str(self):
        """Test Recommendation string representation."""
        rec = Recommendation.objects.create(
            user=self.user,
            category='activity',
            text='Walk more',
            score=0.5
        )
        self.assertIn('testuser', str(rec))
        self.assertIn('activity', str(rec))


class ServiceTests(TestCase):
    """Tests for services layer."""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
    
    def test_compute_features_no_data(self):
        """Test computing features with no metrics."""
        features = compute_features_for_user(self.user.id)
        self.assertEqual(features['sleep_7d_avg'], 0.0)
        self.assertEqual(features['steps_7d_avg'], 0.0)
    
    def test_compute_features_with_data(self):
        """Test computing features with 7 days of data."""
        today = date.today()
        
        # Create 7 days of metrics
        for i in range(7):
            DailyMetrics.objects.create(
                user=self.user,
                date=today - timedelta(days=i),
                steps=5000,
                sleep_hours=6.0,
                systolic_bp=120,
                diastolic_bp=80
            )
        
        features = compute_features_for_user(self.user.id)
        self.assertEqual(features['sleep_7d_avg'], 6.0)
        self.assertEqual(features['steps_7d_avg'], 5000.0)
        self.assertEqual(features['latest_sbp'], 120)
        self.assertEqual(features['latest_dbp'], 80)
    
    def test_generate_recommendations_low_sleep(self):
        """Test that low sleep triggers sleep recommendation."""
        today = date.today()
        
        # Create 7 days of low sleep metrics
        for i in range(7):
            DailyMetrics.objects.create(
                user=self.user,
                date=today - timedelta(days=i),
                steps=5000,
                sleep_hours=5.5  # Below 6.0 threshold
            )
        
        features = compute_features_for_user(self.user.id)
        count = generate_recommendations_for_user(self.user.id, features)
        
        self.assertGreater(count, 0)
        
        # Check that sleep recommendation was created
        sleep_recs = Recommendation.objects.filter(user=self.user, category='sleep')
        self.assertTrue(sleep_recs.exists())
    
    def test_generate_recommendations_low_steps(self):
        """Test that low steps triggers activity recommendation."""
        today = date.today()
        
        # Create 7 days of low activity metrics
        for i in range(7):
            DailyMetrics.objects.create(
                user=self.user,
                date=today - timedelta(days=i),
                steps=4000,  # Below 5000 threshold
                sleep_hours=7.0
            )
        
        features = compute_features_for_user(self.user.id)
        count = generate_recommendations_for_user(self.user.id, features)
        
        self.assertGreater(count, 0)
        
        # Check that activity recommendation was created
        activity_recs = Recommendation.objects.filter(user=self.user, category='activity')
        self.assertTrue(activity_recs.exists())
    
    def test_generate_recommendations_high_bp(self):
        """Test that high BP triggers lifestyle alert."""
        today = date.today()
        
        DailyMetrics.objects.create(
            user=self.user,
            date=today,
            systolic_bp=185,  # Above 180 threshold
            diastolic_bp=125   # Above 120 threshold
        )
        
        features = compute_features_for_user(self.user.id)
        count = generate_recommendations_for_user(self.user.id, features)
        
        self.assertGreater(count, 0)
        
        # Check that high-priority BP alert was created
        bp_recs = Recommendation.objects.filter(user=self.user, category='lifestyle', score=1.0)
        self.assertTrue(bp_recs.exists())


class EngineTests(TestCase):
    """Tests for recommendation engine rules."""
    
    def test_rules_returns_list(self):
        """Test that rules() returns a list of callables."""
        rule_list = rules()
        self.assertIsInstance(rule_list, list)
        self.assertGreater(len(rule_list), 0)
        for rule in rule_list:
            self.assertTrue(callable(rule))
    
    def test_sleep_short_rule(self):
        """Test sleep_short rule triggers correctly."""
        rule_list = rules()
        sleep_rule = rule_list[1]  # sleep_short is second (after bp_alert)
        
        # Should trigger
        result = sleep_rule({'sleep_7d_avg': 5.5})
        self.assertIsNotNone(result)
        self.assertEqual(result['category'], 'sleep')
        
        # Should not trigger
        result = sleep_rule({'sleep_7d_avg': 7.0})
        self.assertIsNone(result)
    
    def test_steps_low_rule(self):
        """Test steps_low rule triggers correctly."""
        rule_list = rules()
        steps_rule = rule_list[2]  # steps_low is third
        
        # Should trigger
        result = steps_rule({'steps_7d_avg': 4000})
        self.assertIsNotNone(result)
        self.assertEqual(result['category'], 'activity')
        
        # Should not trigger
        result = steps_rule({'steps_7d_avg': 6000})
        self.assertIsNone(result)


class APITests(APITestCase):
    """Tests for REST API endpoints."""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client.force_authenticate(user=self.user)
    
    def test_create_daily_metrics(self):
        """Test POST to create daily metrics."""
        url = '/api/metrics/'
        data = {
            'date': date.today().isoformat(),
            'steps': 5000,
            'sleep_hours': 7.0,
            'systolic_bp': 120,
            'diastolic_bp': 80
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(DailyMetrics.objects.count(), 1)
        self.assertEqual(DailyMetrics.objects.first().user, self.user)
    
    def test_list_daily_metrics(self):
        """Test GET to list daily metrics."""
        DailyMetrics.objects.create(
            user=self.user,
            date=date.today(),
            steps=5000
        )
        
        url = '/api/metrics/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_run_recommendations_action(self):
        """Test POST to /api/metrics/run_recommendations/."""
        # Create some metrics first
        today = date.today()
        for i in range(7):
            DailyMetrics.objects.create(
                user=self.user,
                date=today - timedelta(days=i),
                steps=4000,  # Low steps
                sleep_hours=5.5  # Low sleep
            )
        
        url = '/api/metrics/run_recommendations/'
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('generated', response.data)
        self.assertIn('features', response.data)
        self.assertGreater(response.data['generated'], 0)
    
    def test_list_recommendations(self):
        """Test GET to list recommendations."""
        Recommendation.objects.create(
            user=self.user,
            category='activity',
            text='Walk more',
            score=0.5
        )
        
        url = '/api/recommendations/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_recommendations_ordered_by_score(self):
        """Test that recommendations are ordered by score descending."""
        Recommendation.objects.create(
            user=self.user,
            category='activity',
            text='Low priority',
            score=0.3
        )
        Recommendation.objects.create(
            user=self.user,
            category='lifestyle',
            text='High priority',
            score=0.9
        )
        
        url = '/api/recommendations/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        self.assertEqual(results[0]['score'], 0.9)
        self.assertEqual(results[1]['score'], 0.3)
    
    def test_unauthenticated_access_denied(self):
        """Test that unauthenticated users cannot access API."""
        self.client.force_authenticate(user=None)
        
        url = '/api/metrics/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_user_can_only_see_own_metrics(self):
        """Test that users can only see their own metrics."""
        other_user = User.objects.create_user(username='other', password='testpass123')
        
        DailyMetrics.objects.create(user=self.user, date=date.today(), steps=5000)
        DailyMetrics.objects.create(user=other_user, date=date.today(), steps=6000)
        
        url = '/api/metrics/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['username'], 'testuser')
