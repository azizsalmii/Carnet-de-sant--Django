"""
Advanced feature engineering for health metrics.

Computes rich features for ML model training including trends,
variability, correlations, and temporal patterns.
"""
from datetime import timedelta
from typing import Dict, List, Optional
import logging
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import DailyMetrics, Profile

User = get_user_model()
logger = logging.getLogger(__name__)


class FeatureEngineer:
    """Advanced feature computation for health metrics."""
    
    @staticmethod
    def compute_rolling_stats(values: List[float], windows: List[int] = [7, 14, 30]) -> Dict:
        """
        Compute rolling statistics for multiple time windows.
        
        Args:
            values: List of metric values (most recent last)
            windows: List of window sizes in days
            
        Returns:
            Dictionary with rolling stats for each window
        """
        stats = {}
        
        for window in windows:
            window_values = values[-window:] if len(values) >= window else values
            
            if not window_values:
                continue
            
            prefix = f"{window}d"
            stats[f'{prefix}_mean'] = sum(window_values) / len(window_values)
            stats[f'{prefix}_min'] = min(window_values)
            stats[f'{prefix}_max'] = max(window_values)
            
            # Standard deviation
            if len(window_values) > 1:
                mean = stats[f'{prefix}_mean']
                variance = sum((x - mean) ** 2 for x in window_values) / len(window_values)
                stats[f'{prefix}_std'] = variance ** 0.5
            else:
                stats[f'{prefix}_std'] = 0.0
            
            # Coefficient of variation (variability indicator)
            if stats[f'{prefix}_mean'] > 0:
                stats[f'{prefix}_cv'] = stats[f'{prefix}_std'] / stats[f'{prefix}_mean']
            else:
                stats[f'{prefix}_cv'] = 0.0
        
        return stats
    
    @staticmethod
    def compute_trend(values: List[float], days: int = 7) -> Dict:
        """
        Compute trend indicators (increasing, decreasing, stable).
        
        Args:
            values: List of metric values (chronological order)
            days: Number of days to analyze
            
        Returns:
            Dictionary with trend metrics
        """
        recent_values = values[-days:] if len(values) >= days else values
        
        if len(recent_values) < 2:
            return {
                'trend_direction': 'insufficient_data',
                'trend_slope': 0.0,
                'trend_strength': 0.0,
            }
        
        # Simple linear regression (least squares)
        n = len(recent_values)
        x = list(range(n))
        y = recent_values
        
        x_mean = sum(x) / n
        y_mean = sum(y) / n
        
        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        slope = numerator / denominator if denominator != 0 else 0.0
        
        # Determine direction
        if abs(slope) < 0.01 * y_mean:  # Less than 1% change per day
            direction = 'stable'
        elif slope > 0:
            direction = 'increasing'
        else:
            direction = 'decreasing'
        
        # Trend strength (R-squared approximation)
        if denominator != 0:
            y_pred = [slope * (xi - x_mean) + y_mean for xi in x]
            ss_tot = sum((yi - y_mean) ** 2 for yi in y)
            ss_res = sum((y[i] - y_pred[i]) ** 2 for i in range(n))
            r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0
        else:
            r_squared = 0.0
        
        return {
            'trend_direction': direction,
            'trend_slope': slope,
            'trend_strength': max(0.0, min(1.0, r_squared)),  # Clamp to [0, 1]
        }
    
    @staticmethod
    def compute_consistency_score(values: List[float]) -> float:
        """
        Compute consistency score based on coefficient of variation.
        Higher score = more consistent behavior.
        
        Args:
            values: List of metric values
            
        Returns:
            Consistency score (0.0 to 1.0)
        """
        if len(values) < 2:
            return 0.5  # Neutral score
        
        mean = sum(values) / len(values)
        if mean == 0:
            return 0.0
        
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        std = variance ** 0.5
        cv = std / mean
        
        # Convert CV to consistency score (lower CV = higher consistency)
        # Using exponential decay: consistency = e^(-cv)
        import math
        consistency = math.exp(-cv)
        
        return round(consistency, 3)
    
    @staticmethod
    def compute_temporal_features(dates: List, values: List[float]) -> Dict:
        """
        Extract temporal patterns (day of week, weekend vs weekday).
        
        Args:
            dates: List of date objects
            values: Corresponding metric values
            
        Returns:
            Dictionary with temporal features
        """
        if not dates or not values or len(dates) != len(values):
            return {}
        
        weekday_values = []
        weekend_values = []
        
        for date_obj, value in zip(dates, values):
            if date_obj.weekday() < 5:  # Monday=0, Friday=4
                weekday_values.append(value)
            else:
                weekend_values.append(value)
        
        features = {}
        
        if weekday_values:
            features['weekday_avg'] = sum(weekday_values) / len(weekday_values)
        
        if weekend_values:
            features['weekend_avg'] = sum(weekend_values) / len(weekend_values)
        
        if weekday_values and weekend_values:
            features['weekend_weekday_diff'] = features['weekend_avg'] - features['weekday_avg']
        
        return features
    
    @classmethod
    def compute_comprehensive_features(cls, user_id: int, days: int = 30) -> Dict:
        """
        Compute comprehensive feature set for a user.
        
        Args:
            user_id: User ID
            days: Number of days to look back
            
        Returns:
            Dictionary with all computed features
        """
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            logger.error(f"User {user_id} not found")
            return {}
        
        # Get metrics
        start_date = timezone.now().date() - timedelta(days=days)
        metrics_qs = DailyMetrics.objects.filter(
            user=user,
            date__gte=start_date
        ).order_by('date')
        
        if not metrics_qs.exists():
            logger.warning(f"No metrics found for user {user_id}")
            return {'error': 'insufficient_data'}
        
        # Extract data
        dates = [m.date for m in metrics_qs]
        steps_values = [m.steps for m in metrics_qs if m.steps is not None]
        sleep_values = [m.sleep_hours for m in metrics_qs if m.sleep_hours is not None]
        sbp_values = [m.systolic_bp for m in metrics_qs if m.systolic_bp is not None]
        dbp_values = [m.diastolic_bp for m in metrics_qs if m.diastolic_bp is not None]
        
        features = {
            'user_id': user_id,
            'feature_date': timezone.now().date().isoformat(),
            'data_days': len(dates),
        }
        
        # Profile features
        try:
            profile = user.profile
            features['has_profile'] = True
            features['age'] = None
            if profile.birth_date:
                age = (timezone.now().date() - profile.birth_date).days / 365.25
                features['age'] = round(age, 1)
            features['bmi'] = None
            if profile.height_cm and profile.weight_kg:
                height_m = profile.height_cm / 100
                features['bmi'] = round(profile.weight_kg / (height_m ** 2), 1)
        except Profile.DoesNotExist:
            features['has_profile'] = False
        
        # Steps features
        if steps_values:
            features['steps_count'] = len(steps_values)
            features.update({f'steps_{k}': v for k, v in cls.compute_rolling_stats(steps_values).items()})
            features.update({f'steps_{k}': v for k, v in cls.compute_trend(steps_values).items()})
            features['steps_consistency'] = cls.compute_consistency_score(steps_values)
            
            # Temporal patterns
            steps_temporal = cls.compute_temporal_features(
                [m.date for m in metrics_qs if m.steps is not None],
                steps_values
            )
            features.update({f'steps_{k}': v for k, v in steps_temporal.items()})
        
        # Sleep features
        if sleep_values:
            features['sleep_count'] = len(sleep_values)
            features.update({f'sleep_{k}': v for k, v in cls.compute_rolling_stats(sleep_values).items()})
            features.update({f'sleep_{k}': v for k, v in cls.compute_trend(sleep_values).items()})
            features['sleep_consistency'] = cls.compute_consistency_score(sleep_values)
            
            # Sleep quality indicators
            features['sleep_deficit_days'] = sum(1 for s in sleep_values[-7:] if s < 7.0)
            features['sleep_excess_days'] = sum(1 for s in sleep_values[-7:] if s > 9.0)
        
        # Blood pressure features
        if sbp_values and dbp_values:
            features['bp_count'] = min(len(sbp_values), len(dbp_values))
            features.update({f'sbp_{k}': v for k, v in cls.compute_rolling_stats(sbp_values).items()})
            features.update({f'dbp_{k}': v for k, v in cls.compute_rolling_stats(dbp_values).items()})
            
            # Latest BP
            features['sbp_latest'] = sbp_values[-1] if sbp_values else None
            features['dbp_latest'] = dbp_values[-1] if dbp_values else None
            
            # BP categories (following standard guidelines)
            if features['sbp_latest'] and features['dbp_latest']:
                sbp = features['sbp_latest']
                dbp = features['dbp_latest']
                
                if sbp < 120 and dbp < 80:
                    features['bp_category'] = 'normal'
                elif sbp < 130 and dbp < 80:
                    features['bp_category'] = 'elevated'
                elif sbp < 140 or dbp < 90:
                    features['bp_category'] = 'stage1_hypertension'
                elif sbp < 180 or dbp < 120:
                    features['bp_category'] = 'stage2_hypertension'
                else:
                    features['bp_category'] = 'hypertensive_crisis'
        
        # Cross-metric features
        if steps_values and sleep_values:
            # Check if there's enough data for correlation
            if len(steps_values) >= 7 and len(sleep_values) >= 7:
                # Simple correlation indicator
                recent_steps = steps_values[-7:]
                recent_sleep = sleep_values[-7:]
                features['active_well_rested'] = (
                    sum(recent_steps) / len(recent_steps) > 7000 and
                    sum(recent_sleep) / len(recent_sleep) >= 7.0
                )
        
        return features
