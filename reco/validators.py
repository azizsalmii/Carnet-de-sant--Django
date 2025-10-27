"""
Data validation and preprocessing for health metrics.

Ensures data quality before feature computation and model training.
"""
from datetime import date, timedelta
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class HealthDataValidator:
    """Validate and preprocess health metrics data."""
    
    # Physiological bounds (based on medical literature)
    BOUNDS = {
        'steps': (0, 50000),           # Max realistic daily steps
        'sleep_hours': (0, 16),         # Max realistic sleep duration
        'systolic_bp': (70, 250),       # Viable blood pressure range
        'diastolic_bp': (40, 150),      # Viable blood pressure range
        'heart_rate': (30, 220),        # If we add this later
        'weight_kg': (20, 300),         # If tracking weight changes
        'height_cm': (50, 250),         # Valid height range
    }
    
    # Warning thresholds for quality flags
    WARNING_THRESHOLDS = {
        'steps': (500, 30000),          # Warn if too low/high
        'sleep_hours': (3, 12),         # Warn if unusual
        'systolic_bp': (90, 180),       # Warn if outside healthy range
        'diastolic_bp': (60, 120),      # Warn if outside healthy range
    }
    
    @classmethod
    def validate_metric(cls, field: str, value: Optional[float]) -> Tuple[bool, Optional[str]]:
        """
        Validate a single metric value.
        
        Args:
            field: Name of the metric field
            value: Value to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if value is None:
            return True, None  # Null values are allowed
        
        if field not in cls.BOUNDS:
            return True, None  # Unknown field, skip validation
        
        min_val, max_val = cls.BOUNDS[field]
        
        if value < min_val or value > max_val:
            return False, f"{field} value {value} outside valid range [{min_val}, {max_val}]"
        
        return True, None
    
    @classmethod
    def get_quality_flags(cls, field: str, value: Optional[float]) -> List[str]:
        """
        Get quality warning flags for a metric.
        
        Args:
            field: Name of the metric field
            value: Value to check
            
        Returns:
            List of warning flags
        """
        flags = []
        
        if value is None:
            flags.append(f"{field}_missing")
            return flags
        
        # Check if value is outside warning thresholds
        if field in cls.WARNING_THRESHOLDS:
            min_warn, max_warn = cls.WARNING_THRESHOLDS[field]
            if value < min_warn:
                flags.append(f"{field}_low")
            elif value > max_warn:
                flags.append(f"{field}_high")
        
        return flags
    
    @classmethod
    def validate_metrics_dict(cls, metrics: Dict[str, Optional[float]]) -> Tuple[bool, List[str]]:
        """
        Validate a dictionary of metrics.
        
        Args:
            metrics: Dictionary of field_name -> value
            
        Returns:
            Tuple of (all_valid, list_of_errors)
        """
        errors = []
        
        for field, value in metrics.items():
            is_valid, error_msg = cls.validate_metric(field, value)
            if not is_valid:
                errors.append(error_msg)
        
        return len(errors) == 0, errors
    
    @classmethod
    def detect_outliers_zscore(cls, values: List[float], threshold: float = 3.0) -> List[int]:
        """
        Detect outliers using Z-score method.
        
        Args:
            values: List of numeric values
            threshold: Z-score threshold for outlier detection
            
        Returns:
            List of indices that are outliers
        """
        if len(values) < 3:
            return []  # Need minimum data for statistics
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        std = variance ** 0.5
        
        if std == 0:
            return []  # No variation, no outliers
        
        outliers = []
        for i, value in enumerate(values):
            z_score = abs((value - mean) / std)
            if z_score > threshold:
                outliers.append(i)
        
        return outliers
    
    @classmethod
    def check_data_completeness(cls, metrics_list: List[Dict]) -> Dict[str, float]:
        """
        Calculate completeness scores for each metric field.
        
        Args:
            metrics_list: List of metrics dictionaries
            
        Returns:
            Dictionary of field -> completeness_ratio (0.0 to 1.0)
        """
        if not metrics_list:
            return {}
        
        fields = ['steps', 'sleep_hours', 'systolic_bp', 'diastolic_bp']
        completeness = {}
        
        for field in fields:
            non_null_count = sum(1 for m in metrics_list if m.get(field) is not None)
            completeness[field] = non_null_count / len(metrics_list)
        
        return completeness
    
    @classmethod
    def get_data_quality_report(cls, metrics_list: List[Dict]) -> Dict:
        """
        Generate comprehensive data quality report.
        
        Args:
            metrics_list: List of metrics dictionaries with 'date' and metric fields
            
        Returns:
            Dictionary with quality metrics and recommendations
        """
        if not metrics_list:
            return {
                'total_records': 0,
                'quality_score': 0.0,
                'issues': ['No data available'],
            }
        
        completeness = cls.check_data_completeness(metrics_list)
        avg_completeness = sum(completeness.values()) / len(completeness) if completeness else 0
        
        # Check for gaps in date sequence
        dates = sorted([m['date'] for m in metrics_list if 'date' in m])
        gaps = []
        for i in range(len(dates) - 1):
            delta = (dates[i + 1] - dates[i]).days
            if delta > 1:
                gaps.append(f"{delta} days between {dates[i]} and {dates[i+1]}")
        
        # Collect quality flags
        all_flags = []
        for metrics in metrics_list:
            for field in ['steps', 'sleep_hours', 'systolic_bp', 'diastolic_bp']:
                flags = cls.get_quality_flags(field, metrics.get(field))
                all_flags.extend(flags)
        
        # Calculate overall quality score (0-100)
        quality_score = avg_completeness * 100
        if all_flags:
            quality_score -= min(len(set(all_flags)) * 5, 30)  # Deduct for flags
        quality_score = max(0, quality_score)
        
        return {
            'total_records': len(metrics_list),
            'date_range': f"{dates[0]} to {dates[-1]}" if dates else "N/A",
            'completeness': completeness,
            'avg_completeness': round(avg_completeness, 2),
            'quality_score': round(quality_score, 1),
            'date_gaps': gaps,
            'quality_flags': list(set(all_flags)),
            'ready_for_training': quality_score >= 70 and avg_completeness >= 0.8,
        }
