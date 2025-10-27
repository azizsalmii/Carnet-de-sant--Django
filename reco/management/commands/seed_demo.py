"""
Management command to seed demo data for a user.

Creates 7 days of plausible (but low) metrics to trigger recommendations.
"""
from datetime import date, timedelta
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from reco.models import DailyMetrics

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed 7 days of demo metrics for a user'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            required=True,
            help='Username to seed metrics for'
        )

    def handle(self, *args, **options):
        username = options['username']
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(f'User "{username}" does not exist')
        
        # Create 7 days of metrics with low values to trigger recommendations
        today = date.today()
        metrics_to_create = []
        
        for i in range(7):
            metric_date = today - timedelta(days=i)
            
            # Check if metrics already exist for this date
            if DailyMetrics.objects.filter(user=user, date=metric_date).exists():
                self.stdout.write(
                    self.style.WARNING(f'Metrics already exist for {metric_date}, skipping')
                )
                continue
            
            # Low values to trigger recommendations
            metrics_to_create.append(
                DailyMetrics(
                    user=user,
                    date=metric_date,
                    steps=3000 + (i * 200),  # Low step count
                    sleep_hours=5.5 + (i * 0.1),  # Low sleep
                    systolic_bp=120 + (i * 2),  # Normal-ish BP
                    diastolic_bp=75 + i,
                )
            )
        
        if metrics_to_create:
            DailyMetrics.objects.bulk_create(metrics_to_create)
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully created {len(metrics_to_create)} days of metrics for {username}'
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING('No new metrics created (all dates already have data)')
            )
