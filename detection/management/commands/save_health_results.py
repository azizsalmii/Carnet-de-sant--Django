from django.core.management.base import BaseCommand
from detection.services.utils import generate_sample_data
from detection.services.health_detector import DataPreprocessor, IntelligentAnomalyDetector
from detection.services.alert_system import HealthAlertSystem
from detection.models import HealthData, HealthAlert
import pandas as pd

class Command(BaseCommand):
    help = 'Execute complete health analysis and save results to database'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--users',
            type=int,
            default=1000,
            help='Number of users to analyze'
        )
    
    def handle(self, *args, **options):
        num_users = options['users']
        
        self.stdout.write(f'Starting health analysis for {num_users} users...')
        
        try:
            # Generate sample data
            df = generate_sample_data(num_users)
            
            # Data preprocessing
            preprocessor = DataPreprocessor()
            df = preprocessor.calculate_health_score(df)
            features = preprocessor.prepare_features(df)
            
            # Anomaly detection
            detector = IntelligentAnomalyDetector()
            detector.train_models(features)
            detector.detect_anomalies(features)
            df = detector.ensemble_detection(df)
            
            # Alert generation
            alert_system = HealthAlertSystem(df)
            alerts_df = alert_system.generate_alerts()
            
            # Save to database
            self.save_to_database(df, alerts_df)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully analyzed {len(df)} users, '
                    f'detected {df["predicted_anomaly"].sum()} anomalies, '
                    f'generated {len(alerts_df)} alerts'
                )
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error during analysis: {str(e)}')
            )
    
    def save_to_database(self, df, alerts_df):
        """Save results to Django database"""
        # Clear existing data
        HealthData.objects.all().delete()
        
        # Save health data
        health_objects = []
        for _, row in df.iterrows():
            health_objects.append(HealthData(
                user_id=row['user_id'],
                age=row['age'],
                gender=row['gender'],
                sleep_duration=row['sleep_duration'],
                sleep_quality=row['sleep_quality'],
                steps_daily=row['steps_daily'],
                heart_rate_resting=row['heart_rate_resting'],
                blood_pressure_systolic=row['blood_pressure_systolic'],
                stress_level=row['stress_level'],
                bmi=row['bmi'],
                health_score=row['health_score'],
                health_category=row['health_category'],
                is_anomaly=row.get('is_anomaly', False),
                predicted_anomaly=row.get('predicted_anomaly', False),
                anomaly_confidence=row.get('anomaly_confidence', 0.0),
                risk_level=row.get('risk_level', 'Low')
            ))
        
        HealthData.objects.bulk_create(health_objects)
        
        # Save alerts
        alert_objects = []
        for _, alert in alerts_df.iterrows():
            try:
                user = HealthData.objects.get(user_id=alert['user_id'])
                alert_objects.append(HealthAlert(
                    user=user,
                    alert_type=alert['alert_type'],
                    message=alert['message'],
                    severity=alert['severity'],
                    category=alert['category']
                ))
            except HealthData.DoesNotExist:
                continue
        
        HealthAlert.objects.bulk_create(alert_objects)