from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models

class CustomUser(AbstractUser):
    age = models.PositiveIntegerField(null=True, blank=True)
    poids = models.FloatField(null=True, blank=True)
    taille = models.FloatField(null=True, blank=True)
    preferences = models.JSONField(default=dict, blank=True)

    groups = models.ManyToManyField(
        Group,
        related_name="customuser_set",
        blank=True,
        help_text=("The groups this user belongs to."),
        verbose_name=("groups"),
    )

    user_permissions = models.ManyToManyField(
        Permission,
        related_name="customuser_permissions_set",
        blank=True,
        help_text=("Specific permissions for this user."),
        verbose_name=("user permissions"),
    )

    def __str__(self):
        return self.username
