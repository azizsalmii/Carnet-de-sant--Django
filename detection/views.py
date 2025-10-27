from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import pandas as pd
from .services.health_detector import DataPreprocessor, IntelligentAnomalyDetector
from .services.alert_system import HealthAlertSystem
from .services.utils import generate_sample_data, save_models, load_models
from .models import HealthData, HealthAlert

def health_dashboard(request):
    """Vue pour le tableau de bord santé"""
    return render(request, 'detection/dashboard.html')

def health_results(request):
    """Vue pour afficher les résultats"""
    return render(request, 'detection/results.html')

def health_analysis(request):
    """View for health analysis form"""
    return render(request, 'detection/health_analysis.html')

def user_results(request):
    """View for displaying user analysis results"""
    return render(request, 'detection/user_results.html')

@csrf_exempt
def analyze_user_data(request):
    """Analyze individual user health data"""
    if request.method == 'POST':
        try:
            # Get user data from form
            user_data = {
                'age': int(request.POST.get('age')),
                'gender': request.POST.get('gender'),
                'sleep_duration': float(request.POST.get('sleep_duration')),
                'sleep_quality': int(request.POST.get('sleep_quality')),
                'steps_daily': int(request.POST.get('steps_daily')),
                'sedentary_hours': int(request.POST.get('sedentary_hours')),
                'heart_rate_resting': int(request.POST.get('heart_rate_resting')),
                'blood_pressure_systolic': int(request.POST.get('blood_pressure_systolic')),
                'stress_level': int(request.POST.get('stress_level')),
                'bmi': float(request.POST.get('bmi')),
                'water_intake_liters': float(request.POST.get('water_intake_liters', 2)),
                'fruit_vegetable_servings': int(request.POST.get('fruit_vegetable_servings', 3)),
            }
            
            # Add user_id for compatibility
            user_data['user_id'] = 1
            
            # Create DataFrame with user data
            df = pd.DataFrame([user_data])
            
            # Calculate health score
            preprocessor = DataPreprocessor()
            df = preprocessor.calculate_health_score(df)
            
            # Prepare features for anomaly detection
            features = preprocessor.prepare_features(df)
            
            # Try to load trained models
            try:
                preprocessor_loaded, detector, alert_system = load_models()
            except:
                preprocessor_loaded, detector, alert_system = None, None, None
            
            # If no trained model exists, train a new one with sample data
            if detector is None:
                print("No trained models found. Training new models...")
                sample_df = generate_sample_data(1000)
                sample_df = preprocessor.calculate_health_score(sample_df)
                sample_features = preprocessor.prepare_features(sample_df)
                
                detector = IntelligentAnomalyDetector()
                detector.train_models(sample_features)
                
                # Create alert system for sample data
                alert_system = HealthAlertSystem(sample_df)
                
                # Save the newly trained models
                save_models(preprocessor, detector, alert_system)
                print("New models trained and saved successfully")
            
            # Detect anomalies for user data
            detector.detect_anomalies(features)
            df = detector.ensemble_detection(df)
            
            # Generate alerts for the specific user
            alert_system_user = HealthAlertSystem(df)
            alerts_df = alert_system_user.generate_alerts()
            
            # Prepare results for display
            user_row = df.iloc[0]
            
            # Calculate risk level based on health score and anomalies
            health_score = user_row['health_score']
            is_anomaly = user_row.get('predicted_anomaly', False)  # CORRECTION: Cette ligne était mal indentée
            anomaly_confidence = user_row.get('anomaly_confidence', 0.0)

            # Enhanced risk level calculation
            if is_anomaly and anomaly_confidence >= 0.7:
                risk_level = "High"
            elif is_anomaly and anomaly_confidence >= 0.5:
                risk_level = "Medium-High"
            elif health_score < 50:
                risk_level = "Medium"
            elif health_score < 70:
                risk_level = "Low-Medium"
            else:
                risk_level = "Low"

            # Si c'est normal mais le score est bas, ajuster le risk level
            if not is_anomaly and health_score < 60:
                risk_level = "Low-Medium"
            
            # Health metrics assessment with more detailed analysis
            metrics = [
                {
                    'name': 'Sleep Duration',
                    'value': f"{user_row['sleep_duration']:.1f} hours",
                    'assessment': 'Excellent (7-9h)' if 7 <= user_row['sleep_duration'] <= 9 else 
                                 'Good (6-7h)' if 6 <= user_row['sleep_duration'] < 7 else
                                 'Poor (<6h) - Consider improving',
                    'status': 'good' if 7 <= user_row['sleep_duration'] <= 9 else 
                             'warning' if 6 <= user_row['sleep_duration'] < 7 else 'poor'
                },
                {
                    'name': 'Sleep Quality',
                    'value': f"{user_row['sleep_quality']}/10",
                    'assessment': 'Excellent (8-10)' if user_row['sleep_quality'] >= 8 else
                                 'Good (6-7)' if user_row['sleep_quality'] >= 6 else
                                 'Poor (<6) - Consider improving sleep habits',
                    'status': 'good' if user_row['sleep_quality'] >= 8 else
                             'warning' if user_row['sleep_quality'] >= 6 else 'poor'
                },
                {
                    'name': 'Daily Steps',
                    'value': f"{user_row['steps_daily']:,}",
                    'assessment': 'Excellent (10,000+)' if user_row['steps_daily'] >= 10000 else
                                 'Good (7,500-10,000)' if user_row['steps_daily'] >= 7500 else
                                 'Fair (5,000-7,500)' if user_row['steps_daily'] >= 5000 else
                                 'Poor (<5,000) - Consider increasing activity',
                    'status': 'good' if user_row['steps_daily'] >= 10000 else
                             'warning' if user_row['steps_daily'] >= 5000 else 'poor'
                },
                {
                    'name': 'Resting Heart Rate',
                    'value': f"{user_row['heart_rate_resting']} bpm",
                    'assessment': 'Excellent (60-70 bpm)' if 60 <= user_row['heart_rate_resting'] <= 70 else
                                 'Good (70-80 bpm)' if 70 < user_row['heart_rate_resting'] <= 80 else
                                 'Fair (80-90 bpm)' if 80 < user_row['heart_rate_resting'] <= 90 else
                                 'Poor (>90 bpm) - Monitor closely',
                    'status': 'good' if 60 <= user_row['heart_rate_resting'] <= 70 else
                             'warning' if user_row['heart_rate_resting'] <= 90 else 'poor'
                },
                {
                    'name': 'Blood Pressure',
                    'value': f"{user_row['blood_pressure_systolic']} mmHg",
                    'assessment': 'Normal (<120)' if user_row['blood_pressure_systolic'] < 120 else
                                 'Elevated (120-129)' if user_row['blood_pressure_systolic'] <= 129 else
                                 'High (130-139)' if user_row['blood_pressure_systolic'] <= 139 else
                                 'Very High (≥140) - Consult doctor',
                    'status': 'good' if user_row['blood_pressure_systolic'] < 120 else
                             'warning' if user_row['blood_pressure_systolic'] <= 139 else 'poor'
                },
                {
                    'name': 'Stress Level',
                    'value': f"{user_row['stress_level']}/10",
                    'assessment': 'Low (1-3)' if user_row['stress_level'] <= 3 else
                                 'Moderate (4-6)' if user_row['stress_level'] <= 6 else
                                 'High (7-8)' if user_row['stress_level'] <= 8 else
                                 'Very High (9-10) - Consider stress management',
                    'status': 'good' if user_row['stress_level'] <= 3 else
                             'warning' if user_row['stress_level'] <= 8 else 'poor'
                },
                {
                    'name': 'BMI',
                    'value': f"{user_row['bmi']:.1f}",
                    'assessment': 'Normal (18.5-24.9)' if 18.5 <= user_row['bmi'] <= 24.9 else
                                 'Underweight (<18.5)' if user_row['bmi'] < 18.5 else
                                 'Overweight (25-29.9)' if user_row['bmi'] <= 29.9 else
                                 'Obese (≥30) - Consult healthcare provider',
                    'status': 'good' if 18.5 <= user_row['bmi'] <= 24.9 else
                             'warning' if user_row['bmi'] <= 29.9 else 'poor'
                }
            ]
            
            # Enhanced personalized recommendations based on actual metrics
            recommendations = []
            
            # Sleep recommendations
            if user_row['sleep_duration'] < 7:
                recommendations.append("Aim for 7-9 hours of quality sleep per night")
            if user_row['sleep_quality'] < 7:
                recommendations.append("Improve sleep environment: dark, quiet, cool room")
            
            # Activity recommendations
            if user_row['steps_daily'] < 7500:
                recommendations.append("Increase daily walking: try 30-minute brisk walks")
            if user_row['sedentary_hours'] > 8:
                recommendations.append("Reduce sitting time: stand up every 30 minutes")
            
            # Cardiovascular recommendations
            if user_row['heart_rate_resting'] > 80:
                recommendations.append("Practice deep breathing exercises to lower resting heart rate")
            if user_row['blood_pressure_systolic'] > 130:
                recommendations.append("Monitor blood pressure regularly and reduce salt intake")
            
            # Stress and lifestyle recommendations
            if user_row['stress_level'] > 6:
                recommendations.append("Practice stress-reduction: meditation, yoga, or mindfulness")
            if user_row['water_intake_liters'] < 2:
                recommendations.append("Increase water intake to 2-3 liters daily for better hydration")
            if user_row['fruit_vegetable_servings'] < 5:
                recommendations.append("Aim for 5+ servings of colorful fruits and vegetables daily")
            
            # Weight management
            if not 18.5 <= user_row['bmi'] <= 24.9:
                recommendations.append("Consult with healthcare provider for personalized weight management plan")
            
            # General health improvement
            if health_score < 60:
                recommendations.append("Consider comprehensive health check-up with your doctor")
            
            if not recommendations:
                recommendations.append("Maintain your excellent health habits!")
            
            # Prepare alerts for display
            user_alerts = []
            if not alerts_df.empty:
                user_alerts = alerts_df.to_dict('records')
            
            results = {
                'health_score': round(health_score, 1),
                'health_category': str(user_row['health_category']),
                'is_anomaly': is_anomaly,
                'risk_level': risk_level,
                'anomaly_confidence': round(anomaly_confidence * 100, 1),
                'metrics': metrics,
                'alerts': user_alerts,
                'recommendations': recommendations
            }
            
            return render(request, 'detection/user_results.html', {'results': results})
            
        except Exception as e:
            print(f"Error in analyze_user_data: {str(e)}")
            import traceback
            traceback.print_exc()
            return render(request, 'detection/user_results.html', {'error': str(e)})
    
    return redirect('health_analysis')

@csrf_exempt
def detect_anomalies(request):
    """View for detecting anomalies with configurable parameters"""
    if request.method == 'POST':
        try:
            # Get analysis parameters
            users_count = int(request.POST.get('users_count', 1000))
            analysis_type = request.POST.get('analysis_type', 'comprehensive')
            generate_alerts = request.POST.get('generate_alerts') == 'on'
            
            # Generate or load data
            df = generate_sample_data(users_count)
            
            # Data preprocessing
            preprocessor = DataPreprocessor()
            df = preprocessor.calculate_health_score(df)
            features = preprocessor.prepare_features(df)
            
            # Anomaly detection
            detector = IntelligentAnomalyDetector()
            
            # Adjust contamination based on threshold
            threshold = request.POST.get('anomaly_threshold', 'medium')
            contamination = {'low': 0.08, 'medium': 0.12, 'high': 0.15}[threshold]
            
            detector.train_models(features, contamination=contamination)
            detector.detect_anomalies(features)
            df = detector.ensemble_detection(df)
            
            # Generate alerts if requested
            alerts_df = pd.DataFrame()
            if generate_alerts:
                alert_system = HealthAlertSystem(df)
                alerts_df = alert_system.generate_alerts()
            
            # Save models if requested
            if request.POST.get('save_results') == 'on':
                save_models(preprocessor, detector, alert_system if generate_alerts else None)
            
            # Prepare results for display
            results = {
                'total_users': len(df),
                'anomalies_detected': df['predicted_anomaly'].sum(),
                'avg_health_score': round(df['health_score'].mean(), 1),
                'total_alerts': len(alerts_df),
                'critical_alerts': len(alerts_df[alerts_df['severity'] == 'critical']) if not alerts_df.empty else 0,
                'health_distribution': df['health_category'].value_counts().to_dict(),
                'sample_data': df.head(10).to_dict('records'),
                'sample_alerts': alerts_df.head(10).to_dict('records') if not alerts_df.empty else []
            }
            
            return render(request, 'detection/results.html', {'results': results})
            
        except Exception as e:
            return render(request, 'detection/results.html', {'error': str(e)})
    
    return render(request, 'detection/dashboard.html')

@csrf_exempt
def api_detect_anomalies(request):
    """API pour la détection d'anomalies"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Traitement des données reçues
            df = pd.DataFrame([data])
            
            # Charger le préprocesseur
            import joblib
            preprocessor = joblib.load('ml_models/health_preprocessor.pkl')
            
            # Préparer les features
            features = preprocessor.prepare_features(df)
            
            # Charger le détecteur
            detector = joblib.load('ml_models/anomaly_detector_model.pkl')
            
            # Détecter les anomalies
            detector.detect_anomalies(features)
            df = detector.ensemble_detection(df)
            
            return JsonResponse({
                'status': 'success',
                'is_anomaly': bool(df['predicted_anomaly'].iloc[0]),
                'confidence': float(df['anomaly_confidence'].iloc[0]),
                'risk_level': df['risk_level'].iloc[0],
                'health_score': float(df['health_score'].iloc[0])
            })
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'})

def api_get_alerts(request):
    """API pour récupérer les alertes"""
    user_id = request.GET.get('user_id')
    
    try:
        if user_id:
            # Filtrer par utilisateur
            alerts = HealthAlert.objects.filter(user__user_id=user_id)
        else:
            # Toutes les alertes
            alerts = HealthAlert.objects.all()[:50]
        
        alerts_data = []
        for alert in alerts:
            alerts_data.append({
                'user_id': alert.user.user_id,
                'alert_type': alert.alert_type,
                'message': alert.message,
                'severity': alert.severity,
                'category': alert.category,
                'created_at': alert.created_at.isoformat()
            })
        
        return JsonResponse({'status': 'success', 'alerts': alerts_data})
    
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})