# users/views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .forms import CustomUserCreationForm  # <-- garder seulement ça
from ai_models.models import Diagnosis



def signup_view(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Compte créé avec succès.")
            return redirect("home")
    else:
        form = CustomUserCreationForm()
    return render(request, "users/signup.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('profile')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, "Connexion réussie.")
            return redirect('profile')
        else:
            messages.error(request, "Identifiants invalides.")
    else:
        form = AuthenticationForm(request)
    return render(request, 'users/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, "Déconnecté.")
    return redirect('login')


@login_required(login_url='login')
def profile_view(request):
    """
    Page profil avec les diagnostics sauvegardés.
    - diagnostics : les 20 plus récents de l'utilisateur
    - stats       : compte total et par modalité (brain/xray)
    """
    diagnoses_qs = Diagnosis.objects.filter(user=request.user).order_by('-created_at')
    diagnoses = list(diagnoses_qs[:20])

    stats = {
        "total": diagnoses_qs.count(),
        "brain": diagnoses_qs.filter(modality="brain").count(),
        "xray": diagnoses_qs.filter(modality="xray").count(),
        "recent": len(diagnoses),
    }

    context = {
        "diagnoses": diagnoses,
        "stats": stats,
    }
    return render(request, 'users/profile.html', context)
