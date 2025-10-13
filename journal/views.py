from django.shortcuts import render, redirect
from .models import JournalEntry
from datetime import timedelta
from collections import defaultdict

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
    

def generate_intelligent_conclusion(entries):
    if not entries:
        return ["Aucune entrée pour le moment."]

    # Rassembler les infos par catégorie
    stats = defaultdict(lambda: {'count':0, 'total_intensity':0, 'total_duration':timedelta(0)})
    for entry in entries:
        cat = entry.get_category_display()
        stats[cat]['count'] += 1
        if entry.intensity:
            stats[cat]['total_intensity'] += float(entry.intensity)
        if entry.duration:
            stats[cat]['total_duration'] += entry.duration

    # Construire le résumé et analyse
    lines = []
    for cat, data in stats.items():
        avg_intensity = round(data['total_intensity']/data['count'],1) if data['count']>0 else 0
        hours = data['total_duration'].seconds // 3600
        minutes = (data['total_duration'].seconds % 3600) // 60
        lines.append(f"- {data['count']} entrée(s) pour {cat} (intensité moyenne: {avg_intensity}/10), durée totale: {hours}h{minutes}min")

        # Analyse intelligente
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

    return lines  # retourner une liste de lignes directement utilisable dans le template

def journal_page(request):
    if not request.user.is_authenticated:
        return redirect('login_page')

    errors = {}

    if request.method == 'POST':
        category = request.POST.get('category')
        content = request.POST.get('content')
        intensity = request.POST.get('intensity') or None
        duration_str = request.POST.get('duration')
        location = request.POST.get('location')
        tags = request.POST.get('tags')

        if not content:
            errors['content'] = ["Le contenu est obligatoire"]

        duration = None
        if duration_str:
            try:
                hours, minutes = map(int, duration_str.split(":"))
                duration = timedelta(hours=hours, minutes=minutes)
            except:
                errors['duration'] = ["Format de durée invalide, utiliser hh:mm"]

        if not errors:
            JournalEntry.objects.create(
                user=request.user,
                category=category,
                content=content,
                intensity=intensity,
                duration=duration,
                location=location,
                tags=tags
            )
            return redirect('journal_page')

    entries = JournalEntry.objects.filter(user=request.user).order_by('-created_at')
    conclusion_lines = generate_intelligent_conclusion(entries)

    return render(request, 'journal/journal.html', {
        'entries': entries,
        'errors': errors,
        'conclusion_lines': conclusion_lines
    })
