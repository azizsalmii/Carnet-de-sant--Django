"""
API URLs for RECO recommendation system.
Registers DRF ViewSets for REST API access.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api import ProfileViewSet, DailyMetricsViewSet, RecommendationViewSet

# Create a router with trailing slash support (matching Django's APPEND_SLASH=True)
router = DefaultRouter()
router.register(r'profiles', ProfileViewSet, basename='profile')
router.register(r'metrics', DailyMetricsViewSet, basename='dailymetrics')
router.register(r'recommendations', RecommendationViewSet, basename='recommendation')

# The API URLs are determined automatically by the router
urlpatterns = router.urls


