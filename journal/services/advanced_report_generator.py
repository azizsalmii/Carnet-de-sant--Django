import numpy as np
from datetime import datetime, timedelta
from django.utils import timezone
from ..models import HealthData, MonthlyReport
from ..ml.health_predictor import AdvancedHealthPredictor

class AdvancedReportGenerator:
    """Générateur de rapports avec IA avancée"""
    
    def __init__(self):
        self.ai_predictor = AdvancedHealthPredictor()
        self.risk_thresholds = {
            'sleep_duration': (6, 9),
            'sleep_quality': (3, 5),
            'steps_count': (5000, float('inf')),
            'pain_level': (0, 4)
        }
    
    def generate_advanced_analysis(self, health_data_list):
        """Génère une analyse avancée avec ML"""
        if not health_data_list:
            return self._empty_analysis()
        
        # Agrégation des données
        aggregated_data = self._aggregate_health_data(health_data_list)
        
        # Prédiction du score avec ML
        health_score = self.ai_predictor.predict_health_score(aggregated_data)
        
        # Analyse des risques
        risk_factors = self._identify_risk_factors(aggregated_data)
        
        # Recommandations personnalisées
        recommendations = self._generate_ml_recommendations(aggregated_data, risk_factors)
        
        # Détection d'anomalies
        anomalies = self._detect_anomalies(health_data_list)
        
        return {
            'health_score': round(health_score, 1),
            'risk_factors': risk_factors,
            'personalized_recommendations': recommendations,
            'anomalies_detected': anomalies,
            'confidence_level': self._calculate_confidence(health_data_list),
            'predictive_insights': self._generate_predictive_insights(health_data_list)
        }
    
    def _aggregate_health_data(self, health_data_list):
        """Agrège les données santé pour l'analyse"""
        return {
            'sleep_duration': np.mean([d.sleep_duration or 7 for d in health_data_list]),
            'sleep_quality': np.mean([d.sleep_quality or 3 for d in health_data_list]),
            'steps_count': np.mean([d.steps_count or 5000 for d in health_data_list]),
            'exercise_duration': np.mean([d.exercise_duration or 0 for d in health_data_list]),
            'pain_level': np.mean([d.pain_level or 0 for d in health_data_list]),
            'medication_adherence': np.mean([1 if d.medication_adherence else 0 for d in health_data_list])
        }
    
    def _identify_risk_factors(self, aggregated_data):
        """Identifie les facteurs de risque"""
        risks = []
        
        sleep_duration = aggregated_data['sleep_duration']
        if sleep_duration < 6:
            risks.append("Manque chronique de sommeil")
        elif sleep_duration > 9:
            risks.append("Excès de sommeil")
        
        if aggregated_data['pain_level'] > 6:
            risks.append("Douleur chronique sévère")
        
        if aggregated_data['steps_count'] < 3000:
            risks.append("Mode de vie sédentaire")
        
        return risks
    
    def _generate_ml_recommendations(self, data, risk_factors):
        """Génère des recommandations basées sur le ML"""
        recommendations = []
        
        # Recommandations basées sur les données
        if data['sleep_duration'] < 7:
            sleep_deficit = 7 - data['sleep_duration']
            recommendations.append(f"😴 Essayez d'augmenter votre sommeil de {sleep_deficit:.1f}h pour atteindre 7h minimum")
        
        if data['steps_count'] < 5000:
            step_goal = 5000 - data['steps_count']
            recommendations.append(f"🚶‍♂️ Ajoutez {step_goal:.0f} pas par jour pour atteindre l'objectif minimum de 5000 pas")
        
        if data['pain_level'] > 5:
            recommendations.append("😣 Consultez un professionnel pour gérer votre douleur chronique")
        
        # Recommandations basées sur les risques
        if "Manque chronique de sommeil" in risk_factors:
            recommendations.append("🌙 Priorisez votre sommeil : couchez-vous 30 minutes plus tôt")
        
        if "Mode de vie sédentaire" in risk_factors:
            recommendations.append("💺 Interrompez les longues périodes assises toutes les heures")
        
        return recommendations[:5]
    
    def _detect_anomalies(self, health_data_list):
        """Détecte les anomalies dans les données"""
        if len(health_data_list) < 3:
            return []
        
        anomalies = []
        
        # Détection d'écarts importants
        recent_data = health_data_list[:3]
        historical_data = health_data_list[3:]
        
        if historical_data:
            recent_sleep = np.mean([d.sleep_duration or 0 for d in recent_data])
            historical_sleep = np.mean([d.sleep_duration or 0 for d in historical_data])
            
            if abs(recent_sleep - historical_sleep) > 2:
                anomalies.append(f"Changement important du sommeil: {historical_sleep:.1f}h → {recent_sleep:.1f}h")
        
        return anomalies
    
    def _calculate_confidence(self, health_data_list):
        """Calcule le niveau de confiance de l'analyse"""
        data_points = len(health_data_list)
        completeness = self._calculate_data_completeness(health_data_list)
        
        confidence = min(100, (data_points / 10) * 40 + completeness * 60)
        return round(confidence)
    
    def _calculate_data_completeness(self, health_data_list):
        """Calcule le taux de complétion des données"""
        if not health_data_list:
            return 0
        
        total_fields = 0
        filled_fields = 0
        
        for data in health_data_list:
            fields = [data.sleep_duration, data.sleep_quality, data.steps_count, 
                     data.exercise_duration, data.pain_level]
            total_fields += len(fields)
            filled_fields += sum(1 for field in fields if field is not None)
        
        return filled_fields / total_fields if total_fields > 0 else 0
    
    def _generate_predictive_insights(self, health_data_list):
        """Génère des insights prédictifs"""
        if len(health_data_list) < 5:
            return ["Données insuffisantes pour les prédictions"]
        
        insights = []
        
        # Analyse de tendance simple
        sleep_trend = self._analyze_trend([d.sleep_duration or 0 for d in health_data_list])
        if sleep_trend == "deteriorating":
            insights.append("Tendance à la baisse détectée sur la durée du sommeil")
        
        activity_trend = self._analyze_trend([d.steps_count or 0 for d in health_data_list])
        if activity_trend == "improving":
            insights.append("Amélioration constante de l'activité physique")
        
        return insights
    
    def _analyze_trend(self, values):
        """Analyse la tendance d'une série de valeurs"""
        if len(values) < 3:
            return "stable"
        
        recent = values[:3]
        previous = values[3:6] if len(values) >= 6 else values[3:]
        
        if not previous:
            return "stable"
        
        recent_avg = np.mean(recent)
        previous_avg = np.mean(previous)
        
        if recent_avg > previous_avg + (previous_avg * 0.1):
            return "improving"
        elif recent_avg < previous_avg - (previous_avg * 0.1):
            return "deteriorating"
        return "stable"
    
    def _empty_analysis(self):
        """Retourne une analyse vide"""
        return {
            'health_score': 75,
            'risk_factors': [],
            'personalized_recommendations': ["Aucune donnée disponible pour l'analyse"],
            'anomalies_detected': [],
            'confidence_level': 0,
            'predictive_insights': []
        }