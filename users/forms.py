# users/forms.py
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

from .models import UserProfile

User = get_user_model()


class CustomUserCreationForm(UserCreationForm):
    # Champs User
    email = forms.EmailField(required=True, label="Email")

    # Champs profil
    full_name   = forms.CharField(max_length=150, required=False, label="Nom complet")
    birth_date  = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}), label="Date de naissance")
    sex         = forms.ChoiceField(required=False, choices=UserProfile.SEX_CHOICES, label="Sexe")
    blood_group = forms.ChoiceField(required=False, choices=UserProfile.BLOOD_GROUP_CHOICES, label="Groupe sanguin")
    doctor_name = forms.CharField(max_length=150, required=False, label="Médecin traitant")
    photo       = forms.ImageField(required=False, label="Photo de profil")

    class Meta(UserCreationForm.Meta):
        model = User                    # ✅ utilise le user swappé
        fields = ("username", "email", "password1", "password2")

    def save(self, commit=True):
        # Sauvegarde de l'utilisateur
        user = super().save(commit=False)
        user.email = self.cleaned_data.get("email")

        if commit:
            user.save()

        # Crée/Met à jour le profil
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.full_name   = self.cleaned_data.get("full_name") or ""
        profile.birth_date  = self.cleaned_data.get("birth_date")
        profile.sex         = self.cleaned_data.get("sex") or ""
        profile.blood_group = self.cleaned_data.get("blood_group") or ""
        profile.doctor_name = self.cleaned_data.get("doctor_name") or ""

        photo = self.cleaned_data.get("photo")
        if photo:
            profile.photo = photo

        profile.save()
        return user


# Optionnel : si tu veux un login form custom plus tard
class LoginForm(AuthenticationForm):
    pass
