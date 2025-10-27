"""
Management command to export training dataset.

Exports user metrics, computed features, and recommendation feedback
for ML model training.
"""
import json
from pathlib import Path
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone

from reco.models import DailyMetrics, Recommendation
from reco.features import FeatureEngineer
from reco.validators import HealthDataValidator

User = get_user_model()


class Command(BaseCommand):
    help = 'Export training dataset with features and labels'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            default='training_data',
            help='Output directory for training data'
        )
        parser.add_argument(
            '--min-days',
            type=int,
            default=14,
            help='Minimum days of data required per user'
        )
        parser.add_argument(
            '--with-feedback-only',
            action='store_true',
            help='Only include users who have provided feedback'
        )

    def handle(self, *args, **options):
        output_dir = Path(options['output'])
        min_days = options['min_days']
        feedback_only = options['with_feedback_only']
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        self.stdout.write('Collecting training data...')
        
        # Get users with sufficient data
        users = User.objects.all()
        
        if feedback_only:
            # Only users who have given feedback
            users = users.filter(
                recommendations__helpful__isnull=False
            ).distinct()
        
        training_samples = []
        validation_samples = []
        stats = {
            'total_users': 0,
            'users_with_sufficient_data': 0,
            'users_with_feedback': 0,
            'total_samples': 0,
            'quality_issues': [],
        }
        
        for user in users:
            stats['total_users'] += 1
            
            # Check data sufficiency
            metrics_count = DailyMetrics.objects.filter(user=user).count()
            if metrics_count < min_days:
                continue
            
            stats['users_with_sufficient_data'] += 1
            
            # Get metrics for quality report
            metrics_list = list(
                DailyMetrics.objects.filter(user=user).values(
                    'date', 'steps', 'sleep_hours', 'systolic_bp', 'diastolic_bp'
                )
            )
            
            # Data quality check
            quality_report = HealthDataValidator.get_data_quality_report(metrics_list)
            
            if not quality_report.get('ready_for_training', False):
                stats['quality_issues'].append({
                    'user_id': user.id,
                    'quality_score': quality_report['quality_score'],
                    'issues': quality_report.get('quality_flags', [])
                })
                continue
            
            # Compute features
            try:
                features = FeatureEngineer.compute_comprehensive_features(user.id, days=30)
                if 'error' in features:
                    continue
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'Failed to compute features for user {user.id}: {e}')
                )
                continue
            
            # Get recommendations with feedback as labels
            recommendations = Recommendation.objects.filter(user=user)
            
            # Create labels from feedback
            labels = {
                'helpful_recommendations': [],
                'unhelpful_recommendations': [],
                'viewed_recommendations': [],
            }
            
            has_feedback = False
            for rec in recommendations:
                if rec.helpful is not None:
                    has_feedback = True
                    label_rec = {
                        'category': rec.category,
                        'text': rec.text,
                        'score': rec.score,
                        'helpful': rec.helpful,
                        'viewed': rec.viewed,
                    }
                    
                    if rec.helpful:
                        labels['helpful_recommendations'].append(label_rec)
                    else:
                        labels['unhelpful_recommendations'].append(label_rec)
                
                if rec.viewed:
                    labels['viewed_recommendations'].append({
                        'category': rec.category,
                        'score': rec.score,
                    })
            
            if has_feedback:
                stats['users_with_feedback'] += 1
            
            # Create training sample
            sample = {
                'user_id': user.id,
                'username': user.username,
                'features': features,
                'labels': labels,
                'quality_report': quality_report,
                'export_date': timezone.now().isoformat(),
            }
            
            # Split 80/20 train/val based on user_id
            if user.id % 5 == 0:
                validation_samples.append(sample)
            else:
                training_samples.append(sample)
            
            stats['total_samples'] += 1
        
        # Save datasets
        train_file = output_dir / 'train.json'
        val_file = output_dir / 'validation.json'
        stats_file = output_dir / 'export_stats.json'
        
        with open(train_file, 'w') as f:
            json.dump(training_samples, f, indent=2)
        
        with open(val_file, 'w') as f:
            json.dump(validation_samples, f, indent=2)
        
        with open(stats_file, 'w') as f:
            json.dump(stats, f, indent=2)
        
        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Training data export complete!\n'
                f'   Total users scanned: {stats["total_users"]}\n'
                f'   Users with sufficient data: {stats["users_with_sufficient_data"]}\n'
                f'   Users with feedback: {stats["users_with_feedback"]}\n'
                f'   Training samples: {len(training_samples)}\n'
                f'   Validation samples: {len(validation_samples)}\n'
                f'   Output directory: {output_dir.absolute()}\n'
            )
        )
        
        if stats['quality_issues']:
            self.stdout.write(
                self.style.WARNING(
                    f'   Data quality issues: {len(stats["quality_issues"])} users\n'
                    f'   (See {stats_file} for details)'
                )
            )
