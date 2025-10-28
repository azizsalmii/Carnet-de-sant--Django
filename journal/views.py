from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from .models import MoodEntry
from collections import defaultdict

# Pages statiques
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


# Génération d'une conclusion intelligente
def generate_mood_conclusion(entries):
    """Générer une conclusion intelligente selon les émotions et intensités"""
    if not entries:
        return ["Aucune entrée pour le moment."]

    stats = {}
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
        'conclusion_lines': conclusion_lines,
        'global_score': global_score
    })
