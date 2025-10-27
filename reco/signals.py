"""
Django signals for automatic user setup.

This module creates demo health data for new users automatically,
ensuring the dashboard and AI recommendations work immediately.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.conf import settings
from datetime import date, timedelta
import random

User = get_user_model()


@receiver(post_save, sender=User)
def create_demo_data_for_new_user(sender, instance, created, **kwargs):
    """
    Create only the user profile for new users.
    
    DEMO DATA DISABLED: Users must enter their own metrics manually.
    
    This ensures:
    - Users start with empty dashboard
    - Users enter real personal data via /add-metrics/
    - AI generates recommendations based on REAL user data
    - Better user engagement and data quality
    
    Only creates:
    - User profile (required for recommendations system)
    
    Note: To re-enable demo data for testing, uncomment the metrics creation code below.
    """
    # Only run for newly created users
    if not created:
        return
    
    # Skip for superuser/staff to avoid cluttering admin accounts
    if instance.is_superuser or instance.is_staff:
        return
    
    from .models import Profile
    
    print(f"🎉 Nouvel utilisateur: {instance.username}")
    print("� Profil créé - Dashboard vide (ajoutez vos métriques via /add-metrics/)")
    
    # Step 1: Create user profile with default health information
    # Users will update this in their profile settings
    _profile, profile_created = Profile.objects.get_or_create(
        user=instance,
        defaults={
            'birth_date': date(1990, 1, 1),  # Default placeholder
            'sex': 'M',
            'height_cm': 170.0,
            'weight_kg': 70.0,
            'activity_level': 'moderate',
            'health_goals': 'health',
        }
    )
    
    if profile_created:
        print("✅ Profil par défaut créé - L'utilisateur doit compléter ses informations")
        print("💡 Pour commencer:")
        print("   1. Allez sur /add-metrics/ pour ajouter vos métriques quotidiennes")
        print("   2. Ajoutez au moins 2-3 jours de données")
        print("   3. Visitez /recommendations/ pour générer vos recommandations IA personnalisées")
    
    # DEMO DATA DISABLED - Users must enter real data
    # To re-enable demo data for testing, uncomment the code below:
    
    # from .models import DailyMetrics
    # today = date.today()
    # metrics_to_create = []
    # 
    # for i in range(7):
    #     metric_date = today - timedelta(days=6-i)
    #     steps = random.randint(2000, 5000)
    #     sleep = round(random.uniform(4.5, 6.8), 1)
    #     sbp = random.randint(130, 155)
    #     dbp = random.randint(82, 98)
    #     
    #     metrics_to_create.append(
    #         DailyMetrics(
    #             user=instance,
    #             date=metric_date,
    #             steps=steps,
    #             sleep_hours=sleep,
    #             systolic_bp=sbp,
    #             diastolic_bp=dbp,
    #         )
    #     )
    # 
    # DailyMetrics.objects.bulk_create(metrics_to_create)
    # print("✅ Demo data created")

