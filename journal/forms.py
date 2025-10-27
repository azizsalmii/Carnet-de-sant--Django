from django import forms
from .models import HealthData, MonthlyReport
from django import forms
from django.utils import timezone
from datetime import date
import re
class HealthDataForm(forms.ModelForm):
    class Meta:
        model = HealthData
        fields = [
            'date', 'symptoms', 'pain_level', 'sleep_duration', 
            'sleep_quality', 'steps_count', 'exercise_duration',
            'activity_type', 'medications', 'medication_adherence',
            'blood_pressure_systolic', 'blood_pressure_diastolic',
            'heart_rate', 'weight'
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'symptoms': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'medications': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'sleep_duration': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'sleep_quality': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '5'}),
            'pain_level': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '10'}),
            'steps_count': forms.NumberInput(attrs={'class': 'form-control'}),
            'exercise_duration': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'activity_type': forms.TextInput(attrs={'class': 'form-control'}),
            'blood_pressure_systolic': forms.NumberInput(attrs={'class': 'form-control'}),
            'blood_pressure_diastolic': forms.NumberInput(attrs={'class': 'form-control'}),
            'heart_rate': forms.NumberInput(attrs={'class': 'form-control'}),
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
        }
        labels = {
            'sleep_duration': 'Durée du sommeil (heures)',
            'sleep_quality': 'Qualité du sommeil (1-5)',
            'pain_level': 'Niveau de douleur (0-10)',
            'steps_count': 'Nombre de pas',
            'exercise_duration': "Durée d'exercice (minutes)",
            'medication_adherence': 'Traitement pris',
        }


class ReportGenerationForm(forms.Form):
    month = forms.CharField(
        widget=forms.TextInput(attrs={
            'type': 'month', 
            'class': 'form-control',
            'required': 'required'
        }),
        help_text="Sélectionnez le mois pour le rapport",
        label="Mois"
    )
    include_ai_analysis = forms.BooleanField(
        initial=True,
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text="Inclure l'analyse IA avancée"
    )
    
    def clean_month(self):
        """Convertit le format YYYY-MM en objet date"""
        month_str = self.cleaned_data['month']
        
        # Vérifier le format avec une regex
        if not re.match(r'^\d{4}-\d{2}$', month_str):
            raise forms.ValidationError("Format de mois invalide. Utilisez le format AAAA-MM.")
        
        try:
            # Convertir "YYYY-MM" en date (premier jour du mois)
            year, month = map(int, month_str.split('-'))
            if month < 1 or month > 12:
                raise forms.ValidationError("Le mois doit être entre 01 et 12.")
            
            month_date = date(year, month, 1)
            return month_date
            
        except ValueError as e:
            raise forms.ValidationError(f"Mois invalide: {str(e)}")