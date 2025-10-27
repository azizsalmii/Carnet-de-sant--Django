import pandas as pd
import numpy as np
import joblib
from sklearn.ensemble import IsolationForest
from sklearn.svm import OneClassSVM
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

class DataPreprocessor:
    def __init__(self):
        self.scaler = StandardScaler()
        self.feature_columns = []
    
    def calculate_health_score(self, df):
        """Calculate comprehensive health score"""
        print("Calculating health scores...")
        
        # Sleep score (0-100)
        sleep_score = np.clip(
            (df['sleep_duration'] / 9) * 40 + 
            (df['sleep_quality'] / 10) * 30, 0, 100
        )
        
        # Activity score (0-100)
        activity_score = np.clip(
            (df['steps_daily'] / 10000) * 50 +
            ((10 - df['sedentary_hours']) / 10) * 50, 0, 100
        )
        
        # Cardiac score (0-100)
        cardiac_score = np.clip(
            (1 - (np.abs(df['heart_rate_resting'] - 65) / 65)) * 50 +
            (1 - (np.abs(df['blood_pressure_systolic'] - 120) / 80)) * 50, 0, 100
        )
        
        # Lifestyle score (0-100)
        lifestyle_score = np.clip(
            ((10 - df['stress_level']) / 10) * 40 +
            (df['bmi'].apply(lambda x: 60 if 18.5 <= x <= 25 else 20)), 0, 100
        )
        
        # Debug print
        print(f"Sleep Score: {sleep_score.values}")
        print(f"Activity Score: {activity_score.values}")
        print(f"Cardiac Score: {cardiac_score.values}")
        print(f"Lifestyle Score: {lifestyle_score.values}")
        
        # Composite health score
        df['health_score'] = (
            sleep_score * 0.25 + 
            activity_score * 0.25 + 
            cardiac_score * 0.25 + 
            lifestyle_score * 0.25
        )
        
        df['health_score'] = np.clip(df['health_score'], 0, 100)
        
        # Health category
        df['health_category'] = pd.cut(df['health_score'],
                                     bins=[0, 50, 70, 85, 100],
                                     labels=['Poor', 'Fair', 'Good', 'Excellent'])
        
        print(f"Final Health Score: {df['health_score'].values}")
        print(f"Health Category: {df['health_category'].values}")
        
        return df
    
    def select_features(self):
        """Select features for anomaly detection"""
        self.feature_columns = [
            'sleep_duration', 'sleep_quality',
            'steps_daily', 'sedentary_hours',
            'heart_rate_resting', 'blood_pressure_systolic',
            'stress_level', 'bmi', 'health_score'
        ]
        print(f"{len(self.feature_columns)} features selected")
        return self.feature_columns
    
    def prepare_features(self, df):
        """Prepare and normalize features"""
        print("Preparing features...")
        
        if not self.feature_columns:
            self.select_features()
        
        # Feature matrix
        feature_matrix = df[self.feature_columns].copy()
        
        # Handle missing values
        feature_matrix = feature_matrix.fillna(feature_matrix.mean())
        
        # Normalization
        scaled_features = self.scaler.fit_transform(feature_matrix)
        
        print(f"Features prepared: {scaled_features.shape}")
        return scaled_features

class IntelligentAnomalyDetector:
    def __init__(self):
        self.models = {}
        self.results = {}
        self.performance = {}
    
    def train_models(self, features, contamination=0.12):
        """Train multiple anomaly detection models"""
        print("Training models...")
        
        # Model 1: Isolation Forest
        iso_forest = IsolationForest(
            n_estimators=150,
            contamination=contamination,
            random_state=42,
            verbose=0
        )
        iso_forest.fit(features)
        self.models['isolation_forest'] = iso_forest
        
        # Model 2: One-Class SVM
        oc_svm = OneClassSVM(
            nu=contamination,
            kernel='rbf',
            gamma='scale'
        )
        oc_svm.fit(features)
        self.models['one_class_svm'] = oc_svm
        
        print("Models trained successfully")
        return self.models
    
    def detect_anomalies(self, features):
        """Detect anomalies using all trained models"""
        print("Detecting anomalies...")
        
        for model_name, model in self.models.items():
            if hasattr(model, 'predict'):
                predictions = model.predict(features)
                anomalies = predictions == -1
                self.results[model_name] = anomalies
                print(f"  {model_name}: {anomalies.sum():>4} anomalies detected")
        
        return self.results
    
    def ensemble_detection(self, df):
        """Combine results from all models with proper confidence calculation"""
        print("Combining predictions...")
        
        if not self.results:
            print("No detection results available")
            # Fallback: use health score to determine anomalies
            health_score = df['health_score'].iloc[0]
            if health_score < 30:
                df['anomaly_confidence'] = 0.9  # 90% confidence for critical health
                df['predicted_anomaly'] = True
            elif health_score < 50:
                df['anomaly_confidence'] = 0.7  # 70% confidence for poor health
                df['predicted_anomaly'] = True
            else:
                df['anomaly_confidence'] = 0.0
                df['predicted_anomaly'] = False
        else:
            # Ensemble anomaly score - count how many models detected anomaly
            anomaly_scores = np.zeros(len(df))
            
            for model_name, anomalies in self.results.items():
                anomaly_scores += anomalies.astype(int)
                print(f"  {model_name} anomalies: {anomalies.sum()}")
            
            # Normalized confidence score (0 to 1)
            max_score = len(self.models)
            df['anomaly_confidence'] = anomaly_scores / max_score
            
            # Final prediction (majority vote)
            df['predicted_anomaly'] = df['anomaly_confidence'] >= 0.5
        
        # EMERGENCY FIX: Override based on critical health metrics
        user_row = df.iloc[0]
        
        # Check for critical health conditions
        critical_conditions = 0
        total_conditions = 7
        
        if user_row['sleep_duration'] < 4:
            critical_conditions += 1
        if user_row['heart_rate_resting'] > 100:
            critical_conditions += 1
        if user_row['blood_pressure_systolic'] > 140:
            critical_conditions += 1
        if user_row['stress_level'] > 8:
            critical_conditions += 1
        if user_row['steps_daily'] < 2000:
            critical_conditions += 1
        if user_row['bmi'] > 30 or user_row['bmi'] < 18.5:
            critical_conditions += 1
        if user_row['health_score'] < 40:
            critical_conditions += 1
        
        # If multiple critical conditions, force anomaly detection
        if critical_conditions >= 3:
            df['anomaly_confidence'] = max(df['anomaly_confidence'].iloc[0], 0.8)
            df['predicted_anomaly'] = True
            print(f"EMERGENCY: {critical_conditions}/{total_conditions} critical conditions detected!")
        
        # Enhanced risk levels based on confidence and health score
        def calculate_risk_level(row):
            confidence = row['anomaly_confidence']
            health_score = row['health_score']
            
            if confidence >= 0.7 or health_score < 30:
                return 'CRITICAL'
            elif confidence >= 0.5 or health_score < 50:
                return 'HIGH'
            elif confidence >= 0.3 or health_score < 60:
                return 'MEDIUM'
            elif confidence >= 0.1 or health_score < 70:
                return 'LOW'
            else:
                return 'VERY LOW'
        
        df['risk_level'] = df.apply(calculate_risk_level, axis=1)
        
        print(f"=== FINAL RESULTS ===")
        print(f"Health Score: {df['health_score'].iloc[0]}")
        print(f"Anomaly Confidence: {df['anomaly_confidence'].iloc[0]}")
        print(f"Predicted Anomaly: {df['predicted_anomaly'].iloc[0]}")
        print(f"Risk Level: {df['risk_level'].iloc[0]}")
        print(f"Critical Conditions: {critical_conditions}/{total_conditions}")
        
        return df