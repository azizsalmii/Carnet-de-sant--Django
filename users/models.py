from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
from PIL import Image
import os
from django.conf import settings  # ✅ pour AUTH_USER_MODEL

class CustomUser(AbstractUser):
    age = models.PositiveIntegerField(null=True, blank=True)
    poids = models.FloatField(null=True, blank=True)
    taille = models.FloatField(null=True, blank=True)
    preferences = models.JSONField(default=dict, blank=True)

    # Redéfinition avec related_name personnalisés
    groups = models.ManyToManyField(
        Group,
        related_name="customuser_set",
        blank=True,
        help_text="The groups this user belongs to.",
        verbose_name="groups",
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name="customuser_permissions_set",
        blank=True,
        help_text="Specific permissions for this user.",
        verbose_name="user permissions",
    )

    def __str__(self):
        return self.username


def avatar_upload_to(instance, filename):
    # media/avatars/user_<id>/<filename>
    return f"avatars/user_{instance.user_id}/{filename}"


class UserProfile(models.Model):
    SEX_CHOICES = (
        ("M", "Male"),
        ("F", "Female"),
        ("O", "Other"),
    )
    BLOOD_GROUP_CHOICES = (
        ("A+", "A+"), ("A-", "A-"),
        ("B+", "B+"), ("B-", "B-"),
        ("AB+", "AB+"), ("AB-", "AB-"),
        ("O+", "O+"), ("O-", "O-"),
    )

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="user_profile"  # ✅ changé ici pour éviter le conflit
    )

    full_name = models.CharField("Full name", max_length=150, blank=True)
    birth_date = models.DateField("Birth date", null=True, blank=True)
    sex = models.CharField("Gender", max_length=1, choices=SEX_CHOICES, blank=True)
    blood_group = models.CharField("Blood group", max_length=3, choices=BLOOD_GROUP_CHOICES, blank=True)
    doctor_name = models.CharField("Doctor name", max_length=150, blank=True)
    photo = models.ImageField("Profile photo", upload_to=avatar_upload_to, blank=True, null=True)

    def __str__(self):
        return f"Profile of {self.user.username}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Redimensionner l’avatar (max 400x400)
        if self.photo and hasattr(self.photo, "path") and os.path.exists(self.photo.path):
            try:
                img = Image.open(self.photo.path)
                img.thumbnail((400, 400))
                img.save(self.photo.path, optimize=True, quality=85)
            except Exception:
                pass
