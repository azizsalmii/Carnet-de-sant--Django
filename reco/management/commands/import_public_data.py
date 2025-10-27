"""
Import health metrics from public datasets (NHANES, Fitbit, etc.).

Supports:
- NHANES (National Health and Nutrition Examination Survey)
- Fitbit Open Data
- Generic CSV/JSON formats
"""
import csv
import json
from pathlib import Path
from datetime import datetime, date, timedelta
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db import transaction

from reco.models import DailyMetrics, Profile
from reco.validators import HealthDataValidator

User = get_user_model()


class Command(BaseCommand):
    help = 'Import health metrics from public datasets (NHANES, Fitbit, CSV)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--source',
            type=str,
            required=True,
            choices=['nhanes', 'fitbit', 'csv', 'json'],
            help='Data source type'
        )
        parser.add_argument(
            '--file',
            type=str,
            required=True,
            help='Path to data file'
        )
        parser.add_argument(
            '--username-prefix',
            type=str,
            default='imported_user',
            help='Prefix for created usernames'
        )
        parser.add_argument(
            '--validate',
            action='store_true',
            help='Validate data quality before import'
        )
        parser.add_argument(
            '--skip-invalid',
            action='store_true',
            help='Skip invalid records instead of failing'
        )

    def handle(self, *args, **options):
        source = options['source']
        filepath = Path(options['file'])
        username_prefix = options['username_prefix']
        validate = options['validate']
        skip_invalid = options['skip_invalid']
        
        if not filepath.exists():
            raise CommandError(f"File not found: {filepath}")
        
        self.stdout.write(f"Importing from {source}: {filepath}")
        
        # Route to appropriate importer
        if source == 'nhanes':
            stats = self._import_nhanes(filepath, username_prefix, validate, skip_invalid)
        elif source == 'fitbit':
            stats = self._import_fitbit(filepath, username_prefix, validate, skip_invalid)
        elif source == 'csv':
            stats = self._import_csv(filepath, username_prefix, validate, skip_invalid)
        elif source == 'json':
            stats = self._import_json(filepath, username_prefix, validate, skip_invalid)
        
        # Summary
        self.stdout.write(self.style.SUCCESS(
            f"\n✅ Import complete!\n"
            f"   Users created: {stats['users_created']}\n"
            f"   Metrics imported: {stats['metrics_imported']}\n"
            f"   Records skipped: {stats['records_skipped']}\n"
            f"   Validation errors: {stats['validation_errors']}\n"
        ))
        
        if stats.get('quality_warnings'):
            self.stdout.write(
                self.style.WARNING(
                    f"\n⚠️  Quality warnings:\n" +
                    "\n".join(f"   - {w}" for w in stats['quality_warnings'][:10])
                )
            )
    
    def _import_nhanes(self, filepath, username_prefix, validate, skip_invalid):
        """
        Import NHANES data.
        
        Expected CSV columns:
        - SEQN (Respondent sequence number - unique ID)
        - RIDAGEYR (Age in years)
        - RIAGENDR (Gender: 1=Male, 2=Female)
        - BMXHT (Standing height in cm)
        - BMXWT (Weight in kg)
        - BPXSY1 (Systolic BP - 1st reading)
        - BPXDI1 (Diastolic BP - 1st reading)
        - PAQ605 (Vigorous activity days/week)
        - PAD615 (Minutes vigorous activity)
        
        Note: NHANES doesn't have daily time-series data, so we'll create
        a single "snapshot" metric per person.
        """
        stats = {
            'users_created': 0,
            'metrics_imported': 0,
            'records_skipped': 0,
            'validation_errors': 0,
            'quality_warnings': []
        }
        
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            
            for i, row in enumerate(reader, 1):
                try:
                    # Extract NHANES fields
                    seqn = row.get('SEQN', f'unknown_{i}')
                    username = f"{username_prefix}_{seqn}"
                    
                    # Validate required fields
                    if not seqn or seqn == '.':
                        stats['records_skipped'] += 1
                        continue
                    
                    # Create or get user
                    user, created = User.objects.get_or_create(
                        username=username,
                        defaults={'email': f'{username}@nhanes.example.com'}
                    )
                    if created:
                        user.set_password('imported_data')
                        user.save()
                        stats['users_created'] += 1
                    
                    # Extract demographics
                    age = self._safe_float(row.get('RIDAGEYR'))
                    gender_code = self._safe_int(row.get('RIAGENDR'))
                    gender = 'M' if gender_code == 1 else 'F' if gender_code == 2 else 'O'
                    height_cm = self._safe_float(row.get('BMXHT'))
                    weight_kg = self._safe_float(row.get('BMXWT'))
                    
                    # Create/update profile
                    if age or height_cm or weight_kg:
                        birth_year = date.today().year - int(age) if age else None
                        Profile.objects.update_or_create(
                            user=user,
                            defaults={
                                'sex': gender,
                                'birth_date': date(birth_year, 1, 1) if birth_year else None,
                                'height_cm': height_cm,
                                'weight_kg': weight_kg,
                            }
                        )
                    
                    # Extract health metrics
                    systolic_bp = self._safe_int(row.get('BPXSY1'))
                    diastolic_bp = self._safe_int(row.get('BPXDI1'))
                    
                    # Estimate daily steps from activity data
                    vigorous_days = self._safe_float(row.get('PAQ605'))
                    vigorous_mins = self._safe_float(row.get('PAD615'))
                    
                    # Rough estimate: 100 steps per minute of vigorous activity
                    # Average over week: (days * mins * 100) / 7
                    steps = None
                    if vigorous_days and vigorous_mins:
                        steps = int((vigorous_days * vigorous_mins * 100) / 7)
                    
                    # Validate if requested
                    if validate:
                        metrics_dict = {
                            'steps': steps,
                            'systolic_bp': systolic_bp,
                            'diastolic_bp': diastolic_bp,
                        }
                        is_valid, errors = HealthDataValidator.validate_metrics_dict(metrics_dict)
                        
                        if not is_valid:
                            stats['validation_errors'] += 1
                            if skip_invalid:
                                stats['quality_warnings'].append(
                                    f"User {username}: {', '.join(errors)}"
                                )
                                continue
                            else:
                                raise ValueError(f"Validation failed: {errors}")
                    
                    # Create metric (using today as date since NHANES is cross-sectional)
                    metric_date = date.today() - timedelta(days=i % 30)  # Spread over 30 days
                    
                    DailyMetrics.objects.update_or_create(
                        user=user,
                        date=metric_date,
                        defaults={
                            'steps': steps,
                            'systolic_bp': systolic_bp,
                            'diastolic_bp': diastolic_bp,
                            'sleep_hours': None,  # Not in NHANES
                        }
                    )
                    stats['metrics_imported'] += 1
                    
                except Exception as e:
                    if skip_invalid:
                        stats['records_skipped'] += 1
                        stats['quality_warnings'].append(f"Row {i}: {str(e)}")
                    else:
                        raise CommandError(f"Error on row {i}: {e}")
        
        return stats
    
    def _import_fitbit(self, filepath, username_prefix, validate, skip_invalid):
        """
        Import Fitbit Open Data.
        
        Expected CSV columns:
        - Id (User ID)
        - ActivityDate (YYYY-MM-DD)
        - TotalSteps
        - TotalMinutesAsleep (convert to hours)
        - Calories (optional)
        - VeryActiveMinutes, FairlyActiveMinutes, etc.
        """
        stats = {
            'users_created': 0,
            'metrics_imported': 0,
            'records_skipped': 0,
            'validation_errors': 0,
            'quality_warnings': []
        }
        
        user_cache = {}  # Cache users to avoid repeated queries
        
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            
            for i, row in enumerate(reader, 1):
                try:
                    # Extract Fitbit fields
                    user_id = row.get('Id', '').strip()
                    activity_date_str = row.get('ActivityDate', '').strip()
                    
                    if not user_id or not activity_date_str:
                        stats['records_skipped'] += 1
                        continue
                    
                    # Parse date
                    try:
                        activity_date = datetime.strptime(activity_date_str, '%m/%d/%Y').date()
                    except ValueError:
                        try:
                            activity_date = datetime.strptime(activity_date_str, '%Y-%m-%d').date()
                        except ValueError:
                            stats['records_skipped'] += 1
                            continue
                    
                    # Create or get user
                    if user_id not in user_cache:
                        username = f"{username_prefix}_{user_id}"
                        user, created = User.objects.get_or_create(
                            username=username,
                            defaults={'email': f'{username}@fitbit.example.com'}
                        )
                        if created:
                            user.set_password('imported_data')
                            user.save()
                            stats['users_created'] += 1
                        user_cache[user_id] = user
                    else:
                        user = user_cache[user_id]
                    
                    # Extract metrics
                    steps = self._safe_int(row.get('TotalSteps'))
                    minutes_asleep = self._safe_float(row.get('TotalMinutesAsleep'))
                    sleep_hours = minutes_asleep / 60 if minutes_asleep else None
                    
                    # Validate
                    if validate:
                        metrics_dict = {
                            'steps': steps,
                            'sleep_hours': sleep_hours,
                        }
                        is_valid, errors = HealthDataValidator.validate_metrics_dict(metrics_dict)
                        
                        if not is_valid:
                            stats['validation_errors'] += 1
                            if skip_invalid:
                                stats['quality_warnings'].append(
                                    f"User {user.username} on {activity_date}: {', '.join(errors)}"
                                )
                                continue
                    
                    # Create metric
                    DailyMetrics.objects.update_or_create(
                        user=user,
                        date=activity_date,
                        defaults={
                            'steps': steps,
                            'sleep_hours': sleep_hours,
                            'systolic_bp': None,  # Not in Fitbit data
                            'diastolic_bp': None,
                        }
                    )
                    stats['metrics_imported'] += 1
                    
                except Exception as e:
                    if skip_invalid:
                        stats['records_skipped'] += 1
                        stats['quality_warnings'].append(f"Row {i}: {str(e)}")
                    else:
                        raise CommandError(f"Error on row {i}: {e}")
        
        return stats
    
    def _import_csv(self, filepath, username_prefix, validate, skip_invalid):
        """
        Import generic CSV format.
        
        Expected columns:
        - user_id (optional, creates one user per unique ID)
        - date (YYYY-MM-DD)
        - steps
        - sleep_hours
        - systolic_bp
        - diastolic_bp
        """
        stats = {
            'users_created': 0,
            'metrics_imported': 0,
            'records_skipped': 0,
            'validation_errors': 0,
            'quality_warnings': []
        }
        
        user_cache = {}
        
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            
            for i, row in enumerate(reader, 1):
                try:
                    # Get or create user
                    user_id = row.get('user_id', '1')
                    if user_id not in user_cache:
                        username = f"{username_prefix}_{user_id}"
                        user, created = User.objects.get_or_create(
                            username=username,
                            defaults={'email': f'{username}@imported.example.com'}
                        )
                        if created:
                            user.set_password('imported_data')
                            user.save()
                            stats['users_created'] += 1
                        user_cache[user_id] = user
                    else:
                        user = user_cache[user_id]
                    
                    # Parse date
                    date_str = row.get('date', '').strip()
                    metric_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                    
                    # Extract metrics
                    steps = self._safe_int(row.get('steps'))
                    sleep_hours = self._safe_float(row.get('sleep_hours'))
                    systolic_bp = self._safe_int(row.get('systolic_bp'))
                    diastolic_bp = self._safe_int(row.get('diastolic_bp'))
                    
                    # Validate
                    if validate:
                        metrics_dict = {
                            'steps': steps,
                            'sleep_hours': sleep_hours,
                            'systolic_bp': systolic_bp,
                            'diastolic_bp': diastolic_bp,
                        }
                        is_valid, errors = HealthDataValidator.validate_metrics_dict(metrics_dict)
                        
                        if not is_valid:
                            stats['validation_errors'] += 1
                            if skip_invalid:
                                continue
                    
                    # Create metric
                    DailyMetrics.objects.update_or_create(
                        user=user,
                        date=metric_date,
                        defaults={
                            'steps': steps,
                            'sleep_hours': sleep_hours,
                            'systolic_bp': systolic_bp,
                            'diastolic_bp': diastolic_bp,
                        }
                    )
                    stats['metrics_imported'] += 1
                    
                except Exception as e:
                    if skip_invalid:
                        stats['records_skipped'] += 1
                    else:
                        raise CommandError(f"Error on row {i}: {e}")
        
        return stats
    
    def _import_json(self, filepath, username_prefix, validate, skip_invalid):
        """Import from JSON format (array of objects)."""
        stats = {
            'users_created': 0,
            'metrics_imported': 0,
            'records_skipped': 0,
            'validation_errors': 0,
            'quality_warnings': []
        }
        
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            data = [data]
        
        user_cache = {}
        
        for i, record in enumerate(data, 1):
            try:
                user_id = record.get('user_id', '1')
                if user_id not in user_cache:
                    username = f"{username_prefix}_{user_id}"
                    user, created = User.objects.get_or_create(
                        username=username,
                        defaults={'email': f'{username}@imported.example.com'}
                    )
                    if created:
                        user.set_password('imported_data')
                        user.save()
                        stats['users_created'] += 1
                    user_cache[user_id] = user
                else:
                    user = user_cache[user_id]
                
                date_str = record.get('date')
                metric_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                
                steps = record.get('steps')
                sleep_hours = record.get('sleep_hours')
                systolic_bp = record.get('systolic_bp')
                diastolic_bp = record.get('diastolic_bp')
                
                DailyMetrics.objects.update_or_create(
                    user=user,
                    date=metric_date,
                    defaults={
                        'steps': steps,
                        'sleep_hours': sleep_hours,
                        'systolic_bp': systolic_bp,
                        'diastolic_bp': diastolic_bp,
                    }
                )
                stats['metrics_imported'] += 1
                
            except Exception as e:
                if skip_invalid:
                    stats['records_skipped'] += 1
                else:
                    raise CommandError(f"Error on record {i}: {e}")
        
        return stats
    
    def _safe_int(self, value):
        """Safely convert to int, handling missing/invalid values."""
        if not value or value == '.' or value == 'NA':
            return None
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return None
    
    def _safe_float(self, value):
        """Safely convert to float, handling missing/invalid values."""
        if not value or value == '.' or value == 'NA':
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
