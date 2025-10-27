from django.urls import path
from . import views

app_name = 'reco'

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('recommendations/', views.recommendations_view, name='recommendations'),
    path('profile/', views.profile_view, name='profile'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('ai-progress/', views.ai_progress_view, name='ai_progress'),
    path('add-metrics/', views.add_metrics, name='add_metrics'),
]
