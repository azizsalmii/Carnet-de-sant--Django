"""
Script pour réentraîner le modèle LOCALEMENT (sans Google Colab).
Utilisez ce script après avoir collecté 100+ feedbacks.
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report, roc_auc_score
)
import joblib
import json
from datetime import datetime
import os

# Configuration
DATA_FILE = 'training_data.csv'  # Exporté depuis Django
OUTPUT_DIR = 'models/v1/'
MODEL_FILE = 'model_calibrated.joblib'
SCALER_FILE = 'scaler.joblib'
METRICS_FILE = 'metrics.json'

# Features utilisées par le modèle
FEATURE_COLUMNS = [
    'sleep_7d_avg',
    'steps_7d_avg',
    'latest_sbp',
    'latest_dbp',
    'sleep_consistency',
    'activity_trend',
    'bp_category',
    'sleep_deficit',
    'steps_to_goal',
    'age',
    'bmi',
    'days_with_data',
    'category_sleep',
    'category_activity',
    'category_nutrition',
    'category_lifestyle'
]

def load_data():
    """Charger les données de training"""
    print("📂 Chargement des données...")
    
    if not os.path.exists(DATA_FILE):
        print(f"❌ Fichier {DATA_FILE} introuvable!")
        print(f"\n💡 Exportez d'abord vos données:")
        print(f"   python manage.py export_training_data --output {DATA_FILE}")
        return None
    
    df = pd.read_csv(DATA_FILE)
    print(f"✅ Données chargées: {len(df)} lignes, {len(df.columns)} colonnes")
    
    # Vérifier que helpful existe
    if 'helpful' not in df.columns:
        print("❌ Colonne 'helpful' manquante!")
        return None
    
    # Vérifier les features
    missing_cols = [col for col in FEATURE_COLUMNS if col not in df.columns]
    if missing_cols:
        print(f"⚠️ Colonnes manquantes: {missing_cols}")
        print(f"   Disponibles: {df.columns.tolist()}")
        return None
    
    return df

def prepare_data(df):
    """Préparer les features et target"""
    print("\n🔧 Préparation des données...")
    
    # Séparer X et y
    X = df[FEATURE_COLUMNS].copy()
    y = df['helpful'].copy()
    
    # Gérer les valeurs manquantes
    X.fillna(X.median(), inplace=True)
    
    print(f"✅ Features: {X.shape}")
    print(f"✅ Target: {y.shape}")
    print(f"   Classe positive (helpful=True): {(y==True).sum()} ({(y==True).sum()/len(y)*100:.1f}%)")
    print(f"   Classe négative (helpful=False): {(y==False).sum()} ({(y==False).sum()/len(y)*100:.1f}%)")
    
    return X, y

def train_model(X, y):
    """Entraîner le modèle"""
    print("\n🎯 Entraînement du modèle...")
    
    # Split train/test
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"   Train: {X_train.shape[0]} samples")
    print(f"   Test:  {X_test.shape[0]} samples")
    
    # Normalisation
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    print("   ✅ Features normalisées")
    
    # RandomForest
    print("\n🌲 Entraînement RandomForestClassifier...")
    rf_model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1
    )
    rf_model.fit(X_train_scaled, y_train)
    print("   ✅ RandomForest entraîné")
    
    # Calibration
    print("\n⚖️ Calibration du modèle...")
    calibrated_model = CalibratedClassifierCV(
        rf_model,
        method='sigmoid',
        cv=3
    )
    calibrated_model.fit(X_train_scaled, y_train)
    print("   ✅ Modèle calibré")
    
    return calibrated_model, scaler, X_test_scaled, y_test

def evaluate_model(model, X_test, y_test):
    """Évaluer les performances"""
    print("\n📊 Évaluation du modèle...")
    
    # Prédictions
    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    
    # Métriques
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred)
    recall = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    roc_auc = roc_auc_score(y_test, y_pred_proba)
    
    print("\n" + "="*60)
    print("📈 PERFORMANCES DU MODÈLE")
    print("="*60)
    print(f"Accuracy:  {accuracy:.4f} ({accuracy*100:.2f}%)")
    print(f"Precision: {precision:.4f} ({precision*100:.2f}%)")
    print(f"Recall:    {recall:.4f} ({recall*100:.2f}%)")
    print(f"F1-Score:  {f1:.4f} ({f1*100:.2f}%)")
    print(f"ROC-AUC:   {roc_auc:.4f} ({roc_auc*100:.2f}%)")
    print("="*60)
    
    # Classification report
    print("\n📋 Classification Report:")
    print(classification_report(y_test, y_pred, target_names=['Not Helpful', 'Helpful']))
    
    # Confusion matrix
    cm = confusion_matrix(y_test, y_pred)
    print("\n🔢 Matrice de Confusion:")
    print(f"   Vrais Positifs:  {cm[1,1]}")
    print(f"   Vrais Négatifs:  {cm[0,0]}")
    print(f"   Faux Positifs:   {cm[0,1]}")
    print(f"   Faux Négatifs:   {cm[1,0]}")
    
    return {
        'accuracy': float(accuracy),
        'precision': float(precision),
        'recall': float(recall),
        'f1_score': float(f1),
        'roc_auc': float(roc_auc),
        'confusion_matrix': cm.tolist()
    }

def save_model(model, scaler, metrics):
    """Sauvegarder le modèle"""
    print(f"\n💾 Sauvegarde du modèle dans {OUTPUT_DIR}...")
    
    # Créer le dossier si nécessaire
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Sauvegarder le modèle
    model_path = os.path.join(OUTPUT_DIR, MODEL_FILE)
    joblib.dump(model, model_path)
    print(f"   ✅ Modèle: {model_path}")
    
    # Sauvegarder le scaler
    scaler_path = os.path.join(OUTPUT_DIR, SCALER_FILE)
    joblib.dump(scaler, scaler_path)
    print(f"   ✅ Scaler: {scaler_path}")
    
    # Sauvegarder les métriques
    metrics['training_date'] = datetime.now().isoformat()
    metrics['n_features'] = len(FEATURE_COLUMNS)
    metrics['feature_columns'] = FEATURE_COLUMNS
    
    metrics_path = os.path.join(OUTPUT_DIR, METRICS_FILE)
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    print(f"   ✅ Métriques: {metrics_path}")
    
    print("\n🎉 Modèle sauvegardé avec succès!")

def main():
    """Pipeline complet d'entraînement"""
    print("="*60)
    print("🚀 ENTRAÎNEMENT MODÈLE RECO AI (LOCAL)")
    print("="*60)
    
    # 1. Charger les données
    df = load_data()
    if df is None:
        return
    
    # 2. Préparer les données
    X, y = prepare_data(df)
    
    # 3. Entraîner le modèle
    model, scaler, X_test, y_test = train_model(X, y)
    
    # 4. Évaluer
    metrics = evaluate_model(model, X_test, y_test)
    
    # 5. Sauvegarder
    save_model(model, scaler, metrics)
    
    print("\n" + "="*60)
    print("✅ ENTRAÎNEMENT TERMINÉ!")
    print("="*60)
    print("\n💡 Prochaines étapes:")
    print("   1. Vérifiez que les fichiers sont dans models/v1/")
    print("   2. Redémarrez Django: python manage.py runserver")
    print("   3. Testez: python manage.py genrecos --username hamouda")
    print("\n🎯 Le nouveau modèle sera chargé automatiquement!")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Entraînement interrompu par l'utilisateur")
    except Exception as e:
        print(f"\n\n❌ Erreur: {str(e)}")
        import traceback
        traceback.print_exc()
