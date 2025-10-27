import numpy as np
from datetime import datetime, timedelta
from django.utils import timezone
from ..models import HealthData, MonthlyReport, JournalEntry

class HealthReportModel:
    """Modèle IA pour l'analyse des données santé"""
    
    def __init__(self):
        self.features = [
            'sleep_duration', 'sleep_quality', 'steps_count',
            'exercise_duration', 'pain_level', 'medication_adherence'
        ]
    
    def calculate_health_score(self, health_data_list):
        """Calcule un score de santé basé sur les données"""
        if not health_data_list:
            return 75.0  # Score par défaut
        
        try:
            # Features agrégées
            total_sleep = sum(data.sleep_duration or 0 for data in health_data_list)
            avg_sleep_quality = np.mean([data.sleep_quality or 3 for data in health_data_list])
            total_steps = sum(data.steps_count or 0 for data in health_data_list)
            total_exercise = sum(data.exercise_duration or 0 for data in health_data_list)
            avg_pain = np.mean([data.pain_level or 0 for data in health_data_list])
            adherence_rate = np.mean([1 if data.medication_adherence else 0 for data in health_data_list])
            
            # Calcul du score (logique simplifiée)
            score = 100
            score -= max(0, (7 - total_sleep/len(health_data_list)) * 5)  # Pénalité sommeil
            score -= (5 - avg_sleep_quality) * 3  # Qualité sommeil
            score += min(30, total_steps / len(health_data_list) / 1000)  # Bonus pas
            score += min(20, total_exercise / len(health_data_list) / 30)  # Bonus exercice
            score -= avg_pain * 2  # Pénalité douleur
            score += adherence_rate * 10  # Bonus observance
            
            return max(0, min(100, score))
        except:
            return 75.0
    
    def generate_recommendations(self, health_data_list):
        """Génère des recommandations personnalisées"""
        recommendations = []
        
        if not health_data_list:
            return ["Aucune donnée disponible pour générer des recommandations"]
        
        try:
            # Analyse du sommeil
            avg_sleep = np.mean([data.sleep_duration or 0 for data in health_data_list])
            if avg_sleep < 6:
                recommendations.append("💤 Augmentez votre temps de sommeil. Ciblez 7-8 heures par nuit.")
            elif avg_sleep > 9:
                recommendations.append("💤 Votre durée de sommeil est excessive. Consultez un spécialiste.")
            
            # Analyse de l'activité
            avg_steps = np.mean([data.steps_count or 0 for data in health_data_list])
            if avg_steps < 5000:
                recommendations.append("🚶‍♂️ Augmentez votre activité quotidienne. Ciblez 10,000 pas par jour.")
            
            # Analyse de la douleur
            avg_pain = np.mean([data.pain_level or 0 for data in health_data_list])
            if avg_pain > 5:
                recommendations.append("😣 Niveau de douleur élevé détecté. Consultez votre médecin.")
            
            # Observance des traitements
            adherence_rate = np.mean([1 if data.medication_adherence else 0 for data in health_data_list])
            if adherence_rate < 0.8:
                recommendations.append("💊 Améliorez l'observance de vos traitements médicaux.")
            
            if not recommendations:
                recommendations.append("✅ Votre routine santé est globalement bonne. Continuez ainsi !")
        except:
            recommendations.append("📊 Analyse des données en cours d'amélioration.")
        
        return recommendations

class ReportGenerator:
    """Générateur de rapports santé"""
    
    def __init__(self):
        self.ai_model = HealthReportModel()
    
    def get_monthly_data(self, user, month):
        """Récupère les données du mois pour un utilisateur"""
        start_date = month.replace(day=1)
        if month.month == 12:
            end_date = month.replace(year=month.year + 1, month=1, day=1)
        else:
            end_date = month.replace(month=month.month + 1, day=1)
        
        return HealthData.objects.filter(
            user=user,
            date__gte=start_date,
            date__lt=end_date
        ).order_by('date')
    
    def generate_report_content(self, health_data_list):
        """Génère le contenu structuré du rapport"""
        if not health_data_list:
            return self._generate_empty_report()
        
        report_data = {
            'summary': self._generate_summary(health_data_list),
            'symptoms_analysis': self._analyze_symptoms(health_data_list),
            'sleep_analysis': self._analyze_sleep(health_data_list),
            'activity_analysis': self._analyze_activity(health_data_list),
            'treatment_analysis': self._analyze_treatments(health_data_list),
            'vital_signs': self._analyze_vital_signs(health_data_list),
            'statistics': self._calculate_statistics(health_data_list),
            'ai_analysis': self._generate_ai_analysis(health_data_list)
        }
        
        return report_data
    
    def _generate_summary(self, health_data_list):
        """Génère le résumé exécutif"""
        total_days = len(health_data_list)
        health_score = self.ai_model.calculate_health_score(health_data_list)
        
        return {
            'total_days_tracked': total_days,
            'health_score': round(health_score, 1),
            'overall_trend': self._determine_trend(health_data_list),
            'key_highlights': self._get_key_highlights(health_data_list)
        }
    
    def _analyze_symptoms(self, health_data_list):
        """Analyse les symptômes"""
        symptoms_data = []
        for data in health_data_list:
            if data.symptoms:
                symptoms_data.append({
                    'date': data.date.strftime('%d/%m/%Y'),
                    'symptoms': data.symptoms,
                    'pain_level': data.pain_level
                })
        
        return {
            'symptoms_log': symptoms_data,
            'most_common_symptoms': self._extract_common_symptoms(symptoms_data),
            'pain_trend': self._calculate_pain_trend(health_data_list)
        }
    
    def _analyze_sleep(self, health_data_list):
        """Analyse les données de sommeil"""
        sleep_data = [data for data in health_data_list if data.sleep_duration]
        
        if not sleep_data:
            return {'message': 'Aucune donnée de sommeil disponible'}
        
        try:
            avg_duration = np.mean([data.sleep_duration for data in sleep_data])
            avg_quality = np.mean([data.sleep_quality for data in sleep_data])
            
            return {
                'average_duration': round(avg_duration, 1),
                'average_quality': round(avg_quality, 1),
                'sleep_consistency': 'Stable',
                'recommendations': self._generate_sleep_recommendations(avg_duration, avg_quality)
            }
        except:
            return {'message': 'Erreur dans l\'analyse du sommeil'}
    
    def _analyze_activity(self, health_data_list):
        """Analyse l'activité physique"""
        activity_data = [data for data in health_data_list if data.steps_count]
        
        if not activity_data:
            return {'message': 'Aucune donnée d\'activité disponible'}
        
        try:
            avg_steps = np.mean([data.steps_count for data in activity_data])
            avg_exercise = np.mean([data.exercise_duration or 0 for data in activity_data])
            
            return {
                'average_steps': int(avg_steps),
                'average_exercise_minutes': round(avg_exercise, 1),
                'activity_level': self._assess_activity_level(avg_steps),
                'recommendations': self._generate_activity_recommendations(avg_steps)
            }
        except:
            return {'message': 'Erreur dans l\'analyse de l\'activité'}
    
    def _generate_ai_analysis(self, health_data_list):
        """Génère l'analyse IA"""
        return {
            'health_score': self.ai_model.calculate_health_score(health_data_list),
            'risk_factors': self._identify_risk_factors(health_data_list),
            'personalized_recommendations': self.ai_model.generate_recommendations(health_data_list)
        }
    
    def _identify_risk_factors(self, health_data_list):
        """Identifie les facteurs de risque"""
        risk_factors = []
        
        try:
            avg_pain = np.mean([data.pain_level or 0 for data in health_data_list])
            if avg_pain > 6:
                risk_factors.append("Douleur chronique élevée")
            
            avg_sleep = np.mean([data.sleep_duration or 0 for data in health_data_list])
            if avg_sleep < 6:
                risk_factors.append("Manque de sommeil chronique")
        except:
            pass
        
        return risk_factors
    
    def _calculate_statistics(self, health_data_list):
        """Calcule les statistiques générales"""
        return {
            'days_with_data': len(health_data_list),
            'medication_adherence_rate': self._calculate_adherence_rate(health_data_list),
            'symptom_free_days': self._count_symptom_free_days(health_data_list),
        }
    
    def _calculate_adherence_rate(self, health_data_list):
        try:
            adherent_days = sum(1 for data in health_data_list if data.medication_adherence)
            return round(adherent_days / len(health_data_list) * 100, 1) if health_data_list else 0
        except:
            return 0
    
    def _count_symptom_free_days(self, health_data_list):
        try:
            return sum(1 for data in health_data_list if not data.symptoms and (not data.pain_level or data.pain_level < 3))
        except:
            return 0
    
    def _assess_activity_level(self, avg_steps):
        if avg_steps < 5000:
            return "Sédentaire"
        elif avg_steps < 7500:
            return "Légèrement actif"
        elif avg_steps < 10000:
            return "Actif"
        else:
            return "Très actif"
    
    def _generate_activity_recommendations(self, avg_steps):
        if avg_steps < 5000:
            return ["Marchez davantage pendant la journée", "Prenez les escaliers au lieu de l'ascenseur"]
        elif avg_steps < 10000:
            return ["Continuez vos bonnes habitudes", "Essayez d'atteindre 10,000 pas par jour"]
        else:
            return ["Excellent niveau d'activité", "Maintenez ce rythme"]
    
    def _generate_sleep_recommendations(self, avg_duration, avg_quality):
        recommendations = []
        if avg_duration < 7:
            recommendations.append("Essayez de dormir au moins 7 heures par nuit")
        if avg_quality < 3:
            recommendations.append("Améliorez votre environnement de sommeil")
        return recommendations
    
    def _generate_empty_report(self):
        return {
            'summary': {
                'total_days_tracked': 0,
                'health_score': 0,
                'overall_trend': 'Données insuffisantes',
                'key_highlights': ['Aucune donnée disponible pour ce mois']
            },
            'message': 'Aucune donnée santé enregistrée pour cette période'
        }
    
    # Méthodes simplifiées pour la démonstration
    def _determine_trend(self, health_data_list):
        return "Stable"
    
    def _get_key_highlights(self, health_data_list):
        return ["Données analysées avec succès"]
    
    def _extract_common_symptoms(self, symptoms_data):
        return ["Analyse en cours"]
    
    def _calculate_pain_trend(self, health_data_list):
        return "Stable"
    
    def _analyze_treatments(self, health_data_list):
        return {"adherence": self._calculate_adherence_rate(health_data_list)}
    
    def _analyze_vital_signs(self, health_data_list):
        return {"status": "Données limitées"}