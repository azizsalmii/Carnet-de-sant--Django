import pandas as pd

class HealthAlertSystem:
    def __init__(self, df):
        self.df = df
        self.alert_rules = self.define_alert_rules()
    
    def define_alert_rules(self):
        """Define comprehensive health alert rules"""
        return {
            'critical_sleep_deprivation': {
                'condition': 'sleep_duration < 4',
                'message': 'CRITICAL: Severe sleep deprivation (<4 hours)',
                'severity': 'critical',
                'category': 'sleep'
            },
            'poor_sleep_quality': {
                'condition': 'sleep_duration < 6',
                'message': 'ALERT: Insufficient sleep (4-6 hours)',
                'severity': 'high',
                'category': 'sleep'
            },
            'elevated_heart_rate': {
                'condition': 'heart_rate_resting > 100',
                'message': 'ALERT: Elevated resting heart rate (>100 bpm)',
                'severity': 'high',
                'category': 'cardiac'
            },
            'hypertension': {
                'condition': 'blood_pressure_systolic > 140',
                'message': 'ALERT: Hypertension detected (>140 mmHg)',
                'severity': 'high',
                'category': 'cardiac'
            },
            'sedentary_lifestyle': {
                'condition': 'steps_daily < 3000',
                'message': 'WARNING: Very low physical activity (<3000 steps)',
                'severity': 'medium',
                'category': 'activity'
            },
            'high_stress': {
                'condition': 'stress_level > 7',
                'message': 'ALERT: Critical stress levels (>7/10)',
                'severity': 'high',
                'category': 'lifestyle'
            },
            'obesity_risk': {
                'condition': 'bmi > 30',
                'message': 'WARNING: Obesity risk (BMI > 30)',
                'severity': 'medium',
                'category': 'lifestyle'
            },
            'underweight_risk': {
                'condition': 'bmi < 18.5',
                'message': 'WARNING: Underweight risk (BMI < 18.5)',
                'severity': 'medium',
                'category': 'lifestyle'
            },
            'excellent_health': {
                'condition': 'health_score > 85',
                'message': 'POSITIVE: Excellent health score!',
                'severity': 'positive',
                'category': 'overall'
            },
            'poor_health_score': {
                'condition': 'health_score < 50',
                'message': 'CRITICAL: Very low health score',
                'severity': 'critical',
                'category': 'overall'
            }
        }
    
    def evaluate_condition(self, row, condition):
        """Evaluate condition string on row data"""
        return eval(condition, {}, row.to_dict())
    
    def generate_alerts(self):
        """Generate comprehensive health alerts"""
        print("Generating health alerts...")
        
        alerts = []
        for rule_name, rule in self.alert_rules.items():
            mask = self.df.apply(lambda row: self.evaluate_condition(row, rule['condition']), axis=1)
            affected_users = self.df[mask]
            
            for _, user in affected_users.iterrows():
                alerts.append({
                    'user_id': user['user_id'],
                    'alert_type': rule_name,
                    'message': rule['message'],
                    'severity': rule['severity'],
                    'category': rule['category'],
                    'health_score': user['health_score'],
                    'is_anomaly': user.get('predicted_anomaly', False),
                    'risk_level': user.get('risk_level', 'Unknown')
                })
        
        alerts_df = pd.DataFrame(alerts)
        
        # Deduplicate similar alerts
        alerts_df = self._deduplicate_alerts(alerts_df)
        
        print(f"{len(alerts_df)} alerts generated")
        return alerts_df
    
    def _deduplicate_alerts(self, alerts_df):
        """Remove redundant alerts"""
        if alerts_df.empty:
            return alerts_df
            
        # Prioritize most severe alerts
        severity_order = {'critical': 4, 'high': 3, 'medium': 2, 'positive': 1}
        alerts_df['severity_score'] = alerts_df['severity'].map(severity_order)
        
        # Keep most severe alert per category per user
        alerts_df = alerts_df.sort_values('severity_score', ascending=False)
        alerts_df = alerts_df.drop_duplicates(subset=['user_id', 'category'], keep='first')
        
        alerts_df = alerts_df.drop('severity_score', axis=1)
        return alerts_df