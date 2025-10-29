from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from datetime import datetime, timedelta
from collections import defaultdict
from django.http import HttpResponse
from .services.pdf_generator import PDFGenerator

from .models import JournalEntry, HealthData, MonthlyReport
from .forms import HealthDataForm, ReportGenerationForm
from .services.advanced_report_generator import AdvancedReportGenerator
from .services.report_generator import ReportGenerator
def home(request):
    return render(request, 'journal/index.html')

def about(request):
    return render(request, 'journal/about.html')

def appointment(request):
    return render(request, 'journal/appointment.html')

def blog(request):
    return render(request, 'journal/blog.html')

def single_blog(request, pk):
    return render(request, 'journal/single-blog.html')

def contact(request):
    return render(request, 'journal/contact.html')

def gallery(request):
    return render(request, 'journal/gallery.html')

def service(request):
    return render(request, 'journal/service.html')

def team(request):
    return render(request, 'journal/team.html')

# Vues pour le nouveau système de rapports santé

@login_required
def health_data_list(request):
    """Liste des données santé"""
    health_data = HealthData.objects.filter(user=request.user).order_by('-date')
    return render(request, 'journal/health_data_list.html', {
        'health_data': health_data
    })

@login_required
def health_data_create(request):
    """Créer une nouvelle entrée de données santé"""
    if request.method == 'POST':
        form = HealthDataForm(request.POST)
        if form.is_valid():
            health_data = form.save(commit=False)
            health_data.user = request.user
            health_data.save()
            messages.success(request, 'Données santé enregistrées avec succès!')
            return redirect('health_data_list')
    else:
        form = HealthDataForm(initial={'date': datetime.now().date()})
    
    return render(request, 'journal/health_data_form.html', {
        'form': form,
        'title': 'Ajouter des données santé'
    })

@login_required
def health_data_update(request, pk):
    """Modifier une entrée de données santé"""
    health_data = get_object_or_404(HealthData, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = HealthDataForm(request.POST, instance=health_data)
        if form.is_valid():
            form.save()
            messages.success(request, 'Données santé mises à jour avec succès!')
            return redirect('health_data_list')
    else:
        form = HealthDataForm(instance=health_data)
    
    return render(request, 'journal/health_data_form.html', {
        'form': form,
        'title': 'Modifier les données santé'
    })

@login_required
def health_data_delete(request, pk):
    """Supprimer une entrée de données santé"""
    health_data = get_object_or_404(HealthData, pk=pk, user=request.user)
    
    if request.method == 'POST':
        health_data.delete()
        messages.success(request, 'Données santé supprimées avec succès!')
        return redirect('health_data_list')
    
    return render(request, 'journal/health_data_confirm_delete.html', {
        'health_data': health_data
    })

@login_required
def generate_monthly_report(request):
    """Générer un rapport mensuel"""
    if request.method == 'POST':
        form = ReportGenerationForm(request.POST)
        
        if form.is_valid():
            try:
                month = form.cleaned_data['month']
                include_ai = form.cleaned_data['include_ai_analysis']
                
                # Générer le rapport de base avec l'ancien générateur
                generator = ReportGenerator()
                health_data_list = generator.get_monthly_data(request.user, month)
                
                if not health_data_list.exists():
                    messages.warning(
                        request, 
                        f"Aucune donnée santé trouvée pour {month.strftime('%B %Y')}. "
                        f"Ajoutez d'abord des données de santé pour ce mois."
                    )
                    return redirect('health_data_create')
                
                # Générer le contenu de base du rapport
                report_content = generator.generate_report_content(health_data_list)
                
                # Si l'analyse IA avancée est demandée, on la génère et on remplace la partie ai_analysis
                if include_ai:
                    advanced_generator = AdvancedReportGenerator()
                    advanced_analysis = advanced_generator.generate_advanced_analysis(health_data_list)
                    report_content['ai_analysis'] = advanced_analysis
                
                # Sauvegarde du rapport
                report, created = MonthlyReport.objects.get_or_create(
                    user=request.user,
                    month=month,
                    defaults={
                        'report_content': report_content,
                        'health_score': report_content.get('ai_analysis', {}).get('health_score', 0),
                        'recommendations': report_content.get('ai_analysis', {}).get('personalized_recommendations', []),
                        'risk_factors': report_content.get('ai_analysis', {}).get('risk_factors', [])
                    }
                )
                
                if not created:
                    report.report_content = report_content
                    report.health_score = report_content.get('ai_analysis', {}).get('health_score', 0)
                    report.recommendations = report_content.get('ai_analysis', {}).get('personalized_recommendations', [])
                    report.risk_factors = report_content.get('ai_analysis', {}).get('risk_factors', [])
                    report.save()
                
                messages.success(request, f'Rapport pour {month.strftime("%B %Y")} généré avec succès!')
                return redirect('report_detail', pk=report.pk)
                
            except Exception as e:
                messages.error(request, f'Erreur lors de la génération: {str(e)}')
                return redirect('generate_report')
    
    else:
        # Valeur par défaut = mois courant
        current_month = datetime.now().strftime('%Y-%m')
        form = ReportGenerationForm(initial={'month': current_month})
    
    existing_reports = MonthlyReport.objects.filter(user=request.user).order_by('-month')[:5]
    
    return render(request, 'journal/generate_report.html', {
        'form': form,
        'existing_reports': existing_reports
    })
@login_required
def report_detail(request, pk):
    """Détail d'un rapport"""
    report = get_object_or_404(MonthlyReport, pk=pk, user=request.user)
    return render(request, 'journal/report_detail.html', {'report': report})

@login_required
def report_list(request):
    """Liste des rapports"""
    reports = MonthlyReport.objects.filter(user=request.user)
    return render(request, 'journal/report_list.html', {'reports': reports})

# Vues existantes pour le journal (conservées pour la compatibilité)

@login_required
def download_report_pdf(request, pk):
    """Télécharger le rapport en PDF"""
    report = get_object_or_404(MonthlyReport, pk=pk, user=request.user)
    
    try:
        # Récupérer les données santé du mois
        generator = ReportGenerator()
        health_data_list = generator.get_monthly_data(request.user, report.month)
        
        # Générer le PDF
        pdf_generator = PDFGenerator()
        pdf_content = pdf_generator.generate_health_report_pdf(report, health_data_list)
        
        # Créer la réponse HTTP
        response = HttpResponse(pdf_content, content_type='application/pdf')
        filename = f"rapport_sante_{report.month.strftime('%Y_%m')}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
        
    except Exception as e:
        messages.error(request, f"Erreur lors de la génération du PDF: {str(e)}")
        return redirect('report_detail', pk=report.pk)

@login_required
def view_report_pdf(request, pk):
    """Voir le rapport PDF dans le navigateur"""
    report = get_object_or_404(MonthlyReport, pk=pk, user=request.user)
    
    try:
        generator = ReportGenerator()
        health_data_list = generator.get_monthly_data(request.user, report.month)
        
        pdf_generator = PDFGenerator()
        pdf_content = pdf_generator.generate_health_report_pdf(report, health_data_list)
        
        response = HttpResponse(pdf_content, content_type='application/pdf')
        filename = f"rapport_sante_{report.month.strftime('%Y_%m')}.pdf"
        response['Content-Disposition'] = f'inline; filename="{filename}"'
        
        return response
        
    except Exception as e:
        # Fallback: PDF simple
        pdf_generator = PDFGenerator()
        pdf_content = pdf_generator.generate_simple_pdf(report)
        
        response = HttpResponse(pdf_content, content_type='application/pdf')
        response['Content-Disposition'] = 'inline; filename="rapport_sante.pdf"'
        return response
def generate_intelligent_conclusion(entries):
    # Votre fonction existante...
    if not entries:
        return ["Aucune entrée pour le moment."]

    stats = defaultdict(lambda: {'count':0, 'total_intensity':0, 'total_duration':timedelta(0)})
    for entry in entries:
        emo = entry.get_emotion_display() if entry.emotion else "Non analysé"
        if emo not in stats:
            stats[emo] = {'count': 0, 'total_intensity': 0}
        stats[emo]['count'] += 1
        stats[emo]['total_intensity'] += entry.intensity or 0

    lines = []
    for emo, data in stats.items():
        avg_intensity = round(data['total_intensity'] / data['count'], 1)
        lines.append(f"- {data['count']} entrée(s) pour {emo} (intensité moyenne: {avg_intensity}/10)")
        if emo.lower() in ["triste", "stresse", "colere", "anxieux"] and avg_intensity >= 7:
            lines.append(f"⚠️ Attention: tes ressentis {emo} sont intenses. Pense à te détendre ou consulter un professionnel.")
        elif emo.lower() in ["joyeux", "calme"] and avg_intensity >= 7:
            lines.append("😊 Super ! Tu te sens bien, continue comme ça !")
        elif emo.lower() == "fatigue" and avg_intensity >= 5:
            lines.append("😴 Tu sembles fatigué, veille à bien te reposer.")

        if cat.lower() == "symptôme" and avg_intensity >= 7:
            lines.append(f"⚠️ Attention: tes symptômes sont assez intenses (moyenne {avg_intensity}/10). Consulte un médecin si cela persiste.")
        elif cat.lower() == "activité" and avg_intensity < 5:
            lines.append("💪 Essaie d'augmenter légèrement tes activités physiques pour rester en forme.")
        elif cat.lower() == "sommeil" and hours < 6:
            lines.append("😴 Ton sommeil est faible, essaie de dormir plus longtemps pour récupérer.")
        elif cat.lower() == "alimentation":
            lines.append("🥗 Vérifie que ton alimentation est équilibrée et variée.")
        elif cat.lower() == "traitement":
            lines.append("💊 N'oublie pas de suivre tes traitements régulièrement.")

    return lines

# Vue principale pour MoodEntry
@csrf_exempt  # pour tester sans token CSRF (à enlever en prod)
def mood_journal(request):
    if not request.user.is_authenticated:
        return redirect('login_page')

    errors = {}
    if request.method == 'POST':
        emotion = request.POST.get('emotion')
        text = request.POST.get('text')
        intensity = request.POST.get('intensity') or None

        if not emotion:
            errors['emotion'] = ["L'émotion est obligatoire."]
        if intensity:
            try:
                intensity = int(intensity)
                if not 1 <= intensity <= 10:
                    errors['intensity'] = ["L'intensité doit être entre 1 et 10."]
            except ValueError:
                errors['intensity'] = ["L'intensité doit être un nombre entier."]

        if not errors:
            MoodEntry.objects.create(user=request.user, emotion=emotion, text=text, intensity=intensity)
            return redirect('mood_journal')

    entries = MoodEntry.objects.filter(user=request.user)
    conclusion_lines = generate_mood_conclusion(entries)

    # Calcul du score global
    total_score = sum([e.mood_score or 0 for e in entries])
    global_score = round(total_score / len(entries), 1) if entries else 0

    return render(request, 'journal/mood_journal.html', {
        'entries': entries,
        'errors': errors,
        'conclusion_lines': conclusion_lines
    })
