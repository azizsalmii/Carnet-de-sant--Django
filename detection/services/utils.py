import pandas as pd
import numpy as np

def generate_sample_data(num_users=1000):
    """Generate sample health data for testing"""
    np.random.seed(42)
    
    data = {
        'user_id': range(1, num_users + 1),
        'age': np.random.randint(18, 80, num_users),
        'gender': np.random.choice(['Male', 'Female'], num_users),
        'sleep_duration': np.random.normal(7, 1.5, num_users),
        'sleep_quality': np.random.randint(3, 10, num_users),
        'steps_daily': np.random.randint(2000, 15000, num_users),
        'sedentary_hours': np.random.randint(4, 12, num_users),
        'heart_rate_resting': np.random.randint(55, 85, num_users),
        'blood_pressure_systolic': np.random.randint(100, 160, num_users),
        'stress_level': np.random.randint(1, 10, num_users),
        'bmi': np.random.normal(24, 4, num_users)
    }
    
    df = pd.DataFrame(data)
    
    # Clip values to realistic ranges
    df['sleep_duration'] = df['sleep_duration'].clip(2, 12)
    df['bmi'] = df['bmi'].clip(16, 40)
    
    return df

def save_models(preprocessor, detector, alert_system):
    """Save trained models to files"""
    import joblib
    import os
    
    # Create ml_models directory if it doesn't exist
    os.makedirs('ml_models', exist_ok=True)
    
    # Save models
    joblib.dump(preprocessor, 'ml_models/health_preprocessor.pkl')
    joblib.dump(detector, 'ml_models/anomaly_detector_model.pkl')
    joblib.dump(alert_system, 'ml_models/health_alert_system.pkl')
    
    print("Models saved successfully")

def load_models():
    """Load trained models from files"""
    import joblib
    
    try:
        preprocessor = joblib.load('ml_models/health_preprocessor.pkl')
        detector = joblib.load('ml_models/anomaly_detector_model.pkl')
        alert_system = joblib.load('ml_models/health_alert_system.pkl')
        
        print("Models loaded successfully")
        return preprocessor, detector, alert_system
    except Exception as e:
        print(f"Error loading models: {e}")
        return None, None, None