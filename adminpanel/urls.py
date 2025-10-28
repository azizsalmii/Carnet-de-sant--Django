from django.urls import path
from .views import (
    dashboard_home,
    diagnostics_list, diagnostics_user,
    recos_list, recos_user,
    medimgs_list, medimgs_user,
    health_list, health_user,
    users_list,
    # ✅ NEW
    journal_list,
)

app_name = "adminpanel"

urlpatterns = [
    path("", dashboard_home, name="home"),

    # navigation
    path("users/", users_list, name="users"),

    path("diagnostics/", diagnostics_list, name="diagnostics"),
    path("diagnostics/user/<int:user_id>/", diagnostics_user, name="diagnostics_user"),

    path("recommendations/", recos_list, name="recos"),
    path("recommendations/user/<int:user_id>/", recos_user, name="recos_user"),

    path("medical-images/", medimgs_list, name="medimgs"),
    path("medical-images/user/<int:user_id>/", medimgs_user, name="medimgs_user"),

    path("health/", health_list, name="health"),
    path("health/user/<int:user_id>/", health_user, name="health_user"),

    # ✅ NEW: Journal
    path("journal/", journal_list, name="journal"),
]
