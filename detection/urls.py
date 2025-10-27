from django.urls import path
from . import views

urlpatterns = [
path('', views.health_analysis, name='dashboard'),

    path('health_analysis/', views.health_analysis, name='health_analysis'),  # NOUVEAU
    path('analyze-user-data/', views.analyze_user_data, name='analyze_user_data'),  # NOUVEAU
    path('user-results/', views.user_results, name='user_results'),  # NOUVEAU
    path('detect/', views.detect_anomalies, name='detect_anomalies'),
    path('results/', views.health_results, name='health_results'),
    path('api/detect/', views.api_detect_anomalies, name='api_detect_anomalies'),
    path('api/alerts/', views.api_get_alerts, name='api_get_alerts'),
    
]