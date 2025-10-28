# dashboard/views.py
from collections import defaultdict
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required

# Récupérer Diagnosis (ai_models)
try:
    from ai_models.models import Diagnosis
except Exception:
    Diagnosis = None

# Tenter d'importer d'autres modèles s'ils existent chez toi
Recommendation = None
MedicalInfo = None
HealthAnalysis = None

try:
    from reco.models import Recommendation  # adapte si le nom diffère
except Exception:
    pass

try:
    from journal.models import MedicalInfo   # adapte à ton modèle réel
except Exception:
    pass

try:
    from detection.models import HealthAnalysis  # adapte si besoin
except Exception:
    pass


@staff_member_required
def dashboard_home(request):
    """
    Dashboard admin: liste/compte les données des 'users normaux'.
    Par défaut, on considère les utilisateurs non-staff comme 'normaux'.
    """
    # Section DIAGNOSTICS (Brain + CXR)
    diag_by_user = []
    diag_counts = {"total": 0, "brain": 0, "cxr": 0}
    latest_diags = []

    if Diagnosis:
        qs = (Diagnosis.objects
              .select_related("user")
              .order_by("-created_at")[:200])  # limite pour éviter trop de data
        latest_diags = list(qs)

        diag_counts["total"] = qs.count()
        diag_counts["brain"] = qs.filter(modality="brain").count()
        diag_counts["cxr"]   = qs.filter(modality="cxr").count()

        grouped = defaultdict(list)
        for d in qs:
            if d.user and not d.user.is_staff:
                grouped[d.user].append(d)
        # transforme en liste [(user, [diagnostics...])]
        diag_by_user = sorted(grouped.items(), key=lambda x: x[0].username.lower())

    # Section RECOMMENDATIONS (si modèle dispo)
    reco_latest = []
    reco_counts = 0
    if Recommendation:
        try:
            reco_latest = list(
                Recommendation.objects.select_related("user")
                .order_by("-created_at")[:200]
            )
            reco_counts = Recommendation.objects.count()
        except Exception:
            reco_latest = []
            reco_counts = 0

    # Section MEDICAL INFOS (si modèle dispo)
    medinfo_latest = []
    medinfo_counts = 0
    if MedicalInfo:
        try:
            medinfo_latest = list(
                MedicalInfo.objects.select_related("user")
                .order_by("-created_at")[:200]
            )
            medinfo_counts = MedicalInfo.objects.count()
        except Exception:
            pass

    # Section HEALTH ANALYSIS (si modèle dispo)
    health_latest = []
    health_counts = 0
    if HealthAnalysis:
        try:
            health_latest = list(
                HealthAnalysis.objects.select_related("user")
                .order_by("-created_at")[:200]
            )
            health_counts = HealthAnalysis.objects.count()
        except Exception:
            pass

    ctx = {
        "diag_counts": diag_counts,
        "latest_diags": latest_diags,
        "diag_by_user": diag_by_user,

        "reco_latest": reco_latest,
        "reco_counts": reco_counts,

        "medinfo_latest": medinfo_latest,
        "medinfo_counts": medinfo_counts,

        "health_latest": health_latest,
        "health_counts": health_counts,
    }
    return render(request, "dashboard/index.html", ctx)
