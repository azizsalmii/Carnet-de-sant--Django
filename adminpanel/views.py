# adminpanel/views.py

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.db.models import Q, Count, OuterRef, Subquery, IntegerField, Value
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404, render
from django.apps import apps
from django.utils.timezone import now

# pour la détection auto des champs numériques/texte
from django.db.models.fields import (
    CharField, TextField, IntegerField as IntField, FloatField, DecimalField
)

User = get_user_model()

# ============================
# Helpers : modèles & utilitaires
# ============================
def pick_model(app_label, *names):
    """Essaye d'obtenir un modèle par noms connus."""
    for n in names:
        try:
            return apps.get_model(app_label, n)
        except LookupError:
            continue
    return None

def model_has_fields(Model, required=(), any_of=()):
    if not Model:
        return False
    names = {f.name for f in Model._meta.get_fields()}
    if required and not set(required).issubset(names):
        return False
    if any_of and not (set(any_of) & names):
        return False
    return True

def discover_model_by_signature(prefer_app_labels, required_fields=(), any_fields=()):
    """
    Scanne tous les modèles et retourne le meilleur candidat selon une 'signature' de champs.
    """
    candidates = []
    for conf in apps.get_app_configs():
        for M in conf.get_models():
            if model_has_fields(M, required=required_fields, any_of=any_fields):
                score = 0
                # priorité si l'app est préférée
                if conf.label in prefer_app_labels or conf.name.split('.')[-1] in prefer_app_labels:
                    score += 5
                # bonus si le nom du modèle contient des hints
                n = M.__name__.lower()
                for hint in (*required_fields, *any_fields):
                    if hint and hint.lower() in n:
                        score += 1
                candidates.append((score, M))
    if not candidates:
        return None
    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[0][1]

def user_fk_name(Model):
    """Trouve le nom du FK vers User (ex: user/patient/utilisateur/owner)."""
    if not Model:
        return None
    # vrai FK vers le modèle User
    for f in Model._meta.get_fields():
        rel = getattr(f, 'remote_field', None)
        if rel and getattr(rel, 'model', None) == User:
            return f.name
    # heuristique sur des noms fréquents
    for name in ('user', 'patient', 'utilisateur', 'owner'):
        if any(getattr(ff, "name", "") == name for ff in Model._meta.get_fields()):
            return name
    return None

def date_field_name(Model):
    """Choisit un champ date pertinent pour trier."""
    for name in ('created_at', 'date', 'created', 'timestamp', 'updated_at'):
        if any(getattr(f, "name", "") == name for f in Model._meta.get_fields()):
            return name
    return 'id'

def apply_common_filters(qs, Model, request):
    """
    Recherche texte + filtre dates + filtre utilisateur (?user=ID).
    ⚠️ Ne pas appeler après un slice.
    """
    # search
    q = request.GET.get('q', '').strip()
    if q:
        search_fields = [
            'predicted_class', 'modality',
            'summary', 'type', 'notes', 'title', 'content', 'text', 'resume',
            # champs santé probables
            'description', 'details', 'comment', 'comments',
            'value', 'valeur', 'metric', 'reading', 'measure', 'result', 'level',
            'bmi', 'glucose', 'risk', 'risk_score',
        ]
        cond = Q()
        for f in search_fields:
            if any(getattr(ff, "name", "") == f for ff in Model._meta.get_fields()):
                cond |= Q(**{f"{f}__icontains": q})
        if cond:
            qs = qs.filter(cond)

    # dates
    d1 = request.GET.get('from')
    d2 = request.GET.get('to')
    dt = date_field_name(Model)
    if d1:
        qs = qs.filter(**{f"{dt}__date__gte": d1})
    if d2:
        qs = qs.filter(**{f"{dt}__date__lte": d2})

    # user
    u_fk = user_fk_name(Model)
    if u_fk and (u_id := request.GET.get('user')):
        qs = qs.filter(**{f"{u_fk}_id": u_id})

    # tri
    qs = qs.order_by(f"-{date_field_name(Model)}")
    return qs

def paginate(request, qs, per_page=15):
    p = Paginator(qs, per_page)
    page = request.GET.get("page") or 1
    return p.get_page(page)

# ============================
# Helpers d'extraction génériques (score/notes)
# ============================
LIKELY_SCORE_NAMES = (
    "score", "value", "valeur", "metric", "reading", "measure", "result",
    "level", "index", "bmi", "glucose", "bp_systolic", "bp_diastolic",
    "heart_rate", "rmsf", "risk", "risk_score"
)
LIKELY_NOTES_NAMES = (
    "notes", "note", "summary", "resume", "comment", "comments",
    "description", "details", "content", "text", "observation", "observations"
)

def _first_present(o, *names):
    for n in names:
        if hasattr(o, n):
            v = getattr(o, n)
            if v not in (None, ""):
                return v
    return None

def _any_numeric_field_value(o):
    """Retourne la première valeur numérique trouvée (int/float/decimal)."""
    for f in o._meta.get_fields():
        try:
            if isinstance(f, (IntField, FloatField, DecimalField)):
                if f.name in ("id",):
                    continue
                v = getattr(o, f.name, None)
                if v not in (None, ""):
                    return v
        except Exception:
            continue
    return None

def _any_text_field_value(o):
    """Retourne la première valeur textuelle trouvée (char/text) non vide."""
    for f in o._meta.get_fields():
        try:
            if isinstance(f, (CharField, TextField)):
                if f.name in ("title",):
                    continue
                v = getattr(o, f.name, None)
                if v and str(v).strip():
                    return v
        except Exception:
            continue
    return None

# ============================
# Adapters : données → lignes de tableau
# ============================
def rows_for_diagnostics(objs):
    rows = []
    for o in objs:
        rows.append({
            "id": getattr(o, "id", None),
            "date": getattr(o, "created_at", None) or getattr(o, "date", None),
            "user": getattr(o, "user", None) or getattr(o, "patient", None) or getattr(o, "utilisateur", None),
            "modality": getattr(o, "modality", "—"),
            "result": getattr(o, "predicted_class", "—"),
            "conf": getattr(o, "calibrated_confidence", None),
        })
    return rows

def rows_for_recos(objs):
    rows = []
    for o in objs:
        rows.append({
            "id": getattr(o, "id", None),
            "date": getattr(o, "created_at", None) or getattr(o, "date", None),
            "user": getattr(o, "user", None) or getattr(o, "utilisateur", None),
            "rtype": getattr(o, "type", "—"),
            "summary": getattr(o, "summary", None) or getattr(o, "resume", None) or getattr(o, "title", None),
        })
    return rows

def rows_for_medimgs(objs):
    rows = []
    for o in objs:
        rows.append({
            "id": getattr(o, "id", None),
            "date": getattr(o, "created_at", None) or getattr(o, "date", None),
            "user": getattr(o, "user", None) or getattr(o, "patient", None) or getattr(o, "utilisateur", None),
            "kind": getattr(o, "modality", None) or getattr(o, "image_type", None) or "—",
            "path": getattr(o, "image", None) or getattr(o, "file", None),
        })
    return rows

def rows_for_health(objs):
    rows = []
    for o in objs:
        date_v = _first_present(o, "created_at", "date", "timestamp", "updated_at")
        user_v = _first_present(o, "user", "utilisateur", "owner", "patient")
        score_v = _first_present(o, *LIKELY_SCORE_NAMES)
        if score_v is None:
            score_v = _any_numeric_field_value(o)
        notes_v = _first_present(o, *LIKELY_NOTES_NAMES)
        if notes_v is None:
            notes_v = _any_text_field_value(o)
        rows.append({
            "id": getattr(o, "id", None),
            "date": date_v,
            "user": user_v,
            "score": score_v,
            "notes": notes_v,
        })
    return rows

def rows_for_journal(objs):
    rows = []
    for o in objs:
        rows.append({
            "id": getattr(o, "id", None),
            "date": getattr(o, "created_at", None) or getattr(o, "date", None) or getattr(o, "timestamp", None),
            "user": getattr(o, "user", None) or getattr(o, "utilisateur", None) or getattr(o, "owner", None),
            "title": getattr(o, "title", None) or getattr(o, "summary", None) or getattr(o, "resume", None) or "—",
            "text": getattr(o, "content", None) or getattr(o, "text", None) or getattr(o, "notes", None),
        })
    return rows

# ============================
# Détection des modèles (noms connus + fallback signature)
# ============================
Diagnosis      = pick_model('ai_models', 'Diagnosis')
Recommendation = pick_model('reco', 'Recommendation', 'Recommendations')
MedicalImage   = pick_model('journal', 'MedicalImage', 'ImageMedicale', 'ImageMedical')

HealthData     = (
    pick_model('journal', 'DonneesSante', 'DonneeSante', 'DailyMetric', 'DailyMetrics', 'HealthMetric', 'HealthData')
    or discover_model_by_signature(
        prefer_app_labels=['journal'],
        required_fields=(),
        any_fields=('score', 'value', 'metric', 'health', 'donnees', 'sante')
    )
)

JournalEntry = (
    pick_model('journal', 'JournalEntry', 'Journal', 'JournalItem')
    or discover_model_by_signature(
        prefer_app_labels=['journal'],
        required_fields=(),
        any_fields=('title', 'summary', 'resume', 'content', 'text', 'notes')
    )
)

MonthlyReport = (
    pick_model('journal', 'MonthlyReport', 'RapportMensuel', 'MonthlyRapport')
    or discover_model_by_signature(
        prefer_app_labels=['journal'],
        required_fields=(),
        any_fields=('month', 'mois', 'report', 'rapport')
    )
)

# ============================
# Dashboard
# ============================
@staff_member_required
def dashboard_home(request):
    missing = []

    # Diagnostics
    diag_total = diag_brain = diag_cxr = 0
    recent_rows = []
    if Diagnosis:
        base = Diagnosis.objects.all()
        diag_total = base.count()
        diag_brain = base.filter(modality="brain").count()
        diag_cxr   = base.filter(modality__in=["cxr", "chest"]).count()
        recent_diags = Diagnosis.objects.order_by(f"-{date_field_name(Diagnosis)}")[:8]
        recent_rows = rows_for_diagnostics(recent_diags)
    else:
        missing.append("ai_models.Diagnosis")

    # Journal / Images / Health
    health_count = journal_count = images_count = monthly_count = 0

    if HealthData:
        health_count = HealthData.objects.count()
    else:
        missing.append("journal.DonneesSante/HealthData")

    if JournalEntry:
        journal_count = JournalEntry.objects.count()
    else:
        missing.append("journal.JournalEntry")

    if MedicalImage:
        images_count = MedicalImage.objects.count()
    else:
        missing.append("journal.MedicalImage")

    if MonthlyReport:
        monthly_count = MonthlyReport.objects.count()
    else:
        missing.append("journal.MonthlyReport")

    # Recommandations / Profils (optionnels)
    Profile = pick_model('reco', 'Profile', 'Profil', 'UserProfile')
    reco_count = profile_count = 0
    if Recommendation:
        reco_count = Recommendation.objects.count()
    else:
        missing.append("reco.Recommendation")

    if Profile:
        profile_count = Profile.objects.count()
    else:
        missing.append("reco.Profile")

    ctx = {
        "now": now(),
        "diag_total": diag_total,
        "diag_brain": diag_brain,
        "diag_cxr": diag_cxr,
        "recent_rows": recent_rows,
        "health_count": health_count,
        "journal_count": journal_count,
        "images_count": images_count,
        "monthly_count": monthly_count,
        "reco_count": reco_count,
        "profile_count": profile_count,
        "missing_models": missing,
    }
    return render(request, "adminpanel/dashboard.html", ctx)

# ============================
# Diagnostics
# ============================
@staff_member_required
def diagnostics_list(request):
    Model = Diagnosis
    if not Model:
        return render(request, "adminpanel/diagnostics_list.html", {
            "section": "diagnostics", "page_obj": None, "rows": [],
            "user_fk": None, "q": request.GET.get('q', ''), "error": "Modèle Diagnosis introuvable."
        })
    u_fk = user_fk_name(Model)
    qs = Model.objects.all()
    if u_fk:
        qs = qs.select_related(u_fk)
    qs = apply_common_filters(qs, Model, request)
    page_obj = paginate(request, qs)
    rows = rows_for_diagnostics(page_obj.object_list)
    return render(request, "adminpanel/diagnostics_list.html", {
        "section": "diagnostics", "page_obj": page_obj, "rows": rows,
        "user_fk": u_fk, "q": request.GET.get('q', ''),
    })

@staff_member_required
def diagnostics_user(request, user_id):
    Model = Diagnosis
    if not Model:
        return render(request, "adminpanel/diagnostics_list.html", {
            "section": "diagnostics", "page_obj": None, "rows": [],
            "user_fk": None, "q": request.GET.get('q', ''), "error": "Modèle Diagnosis introuvable."
        })
    u_fk = user_fk_name(Model)
    user = get_object_or_404(User, pk=user_id)
    qs = Model.objects.filter(**({f"{u_fk}_id": user_id} if u_fk else {}))
    qs = apply_common_filters(qs, Model, request)
    page_obj = paginate(request, qs)
    rows = rows_for_diagnostics(page_obj.object_list)
    return render(request, "adminpanel/diagnostics_list.html", {
        "section": "diagnostics", "page_obj": page_obj, "rows": rows,
        "user_fk": u_fk, "filter_user": user, "q": request.GET.get('q', ''),
    })

# ============================
# Recommandations
# ============================
@staff_member_required
def recos_list(request):
    Model = Recommendation
    if not Model:
        return render(request, "adminpanel/recos_list.html", {
            "section": "recos", "page_obj": None, "rows": [],
            "user_fk": None, "q": request.GET.get('q', ''), "error": "Modèle Recommendation introuvable."
        })
    u_fk = user_fk_name(Model)
    qs = Model.objects.all()
    if u_fk:
        qs = qs.select_related(u_fk)
    qs = apply_common_filters(qs, Model, request)
    page_obj = paginate(request, qs)
    rows = rows_for_recos(page_obj.object_list)
    return render(request, "adminpanel/recos_list.html", {
        "section": "recos", "page_obj": page_obj, "rows": rows,
        "user_fk": u_fk, "q": request.GET.get('q', ''),
    })

@staff_member_required
def recos_user(request, user_id):
    Model = Recommendation
    if not Model:
        return render(request, "adminpanel/recos_list.html", {
            "section": "recos", "page_obj": None, "rows": [],
            "user_fk": None, "q": request.GET.get('q', ''), "error": "Modèle Recommendation introuvable."
        })
    u_fk = user_fk_name(Model)
    user = get_object_or_404(User, pk=user_id)
    qs = Model.objects.filter(**({f"{u_fk}_id": user_id} if u_fk else {}))
    qs = apply_common_filters(qs, Model, request)
    page_obj = paginate(request, qs)
    rows = rows_for_recos(page_obj.object_list)
    return render(request, "adminpanel/recos_list.html", {
        "section": "recos", "page_obj": page_obj, "rows": rows,
        "user_fk": u_fk, "filter_user": user, "q": request.GET.get('q', ''),
    })

# ============================
# Images médicales
# ============================
@staff_member_required
def medimgs_list(request):
    Model = MedicalImage
    if not Model:
        return render(request, "adminpanel/medimgs_list.html", {
            "section": "medimgs", "page_obj": None, "rows": [],
            "user_fk": None, "q": request.GET.get('q', ''), "error": "Modèle MedicalImage introuvable."
        })
    u_fk = user_fk_name(Model)
    qs = Model.objects.all()
    if u_fk:
        qs = qs.select_related(u_fk)
    qs = apply_common_filters(qs, Model, request)
    page_obj = paginate(request, qs)
    rows = rows_for_medimgs(page_obj.object_list)
    return render(request, "adminpanel/medimgs_list.html", {
        "section": "medimgs", "page_obj": page_obj, "rows": rows,
        "user_fk": u_fk, "q": request.GET.get('q', ''),
    })

@staff_member_required
def medimgs_user(request, user_id):
    Model = MedicalImage
    if not Model:
        return render(request, "adminpanel/medimgs_list.html", {
            "section": "medimgs", "page_obj": None, "rows": [],
            "user_fk": None, "q": request.GET.get('q', ''), "error": "Modèle MedicalImage introuvable."
        })
    u_fk = user_fk_name(Model)
    user = get_object_or_404(User, pk=user_id)
    qs = Model.objects.filter(**({f"{u_fk}_id": user_id} if u_fk else {}))
    qs = apply_common_filters(qs, Model, request)
    page_obj = paginate(request, qs)
    rows = rows_for_medimgs(page_obj.object_list)
    return render(request, "adminpanel/medimgs_list.html", {
        "section": "medimgs", "page_obj": page_obj, "rows": rows,
        "user_fk": u_fk, "filter_user": user, "q": request.GET.get('q', ''),
    })

# ============================
# Données santé
# ============================
@staff_member_required
def health_list(request):
    Model = HealthData
    if not Model:
        return render(request, "adminpanel/health_list.html", {
            "section": "health", "page_obj": None, "rows": [],
            "user_fk": None, "q": request.GET.get('q', ''), "error": "Modèle HealthData introuvable."
        })
    u_fk = user_fk_name(Model)
    qs = Model.objects.all()
    if u_fk:
        qs = qs.select_related(u_fk)
    qs = apply_common_filters(qs, Model, request)
    page_obj = paginate(request, qs)
    rows = rows_for_health(page_obj.object_list)
    return render(request, "adminpanel/health_list.html", {
        "section": "health", "page_obj": page_obj, "rows": rows,
        "user_fk": u_fk, "q": request.GET.get('q', ''),
    })

@staff_member_required
def health_user(request, user_id):
    Model = HealthData
    if not Model:
        return render(request, "adminpanel/health_list.html", {
            "section": "health", "page_obj": None, "rows": [],
            "user_fk": None, "q": request.GET.get('q', ''), "error": "Modèle HealthData introuvable."
        })
    u_fk = user_fk_name(Model)
    user = get_object_or_404(User, pk=user_id)
    qs = Model.objects.filter(**({f"{u_fk}_id": user_id} if u_fk else {}))
    qs = apply_common_filters(qs, Model, request)
    page_obj = paginate(request, qs)
    rows = rows_for_health(page_obj.object_list)
    return render(request, "adminpanel/health_list.html", {
        "section": "health", "page_obj": page_obj, "rows": rows,
        "user_fk": u_fk, "filter_user": user, "q": request.GET.get('q', ''),
    })

# ============================
# Journal
# ============================
@staff_member_required
def journal_list(request):
    Model = JournalEntry
    if not Model:
        return render(request, "adminpanel/journal_list.html", {
            "section": "journal", "page_obj": None, "rows": [],
            "user_fk": None, "q": request.GET.get('q', ''), "error": "Modèle Journal introuvable."
        })
    u_fk = user_fk_name(Model)
    qs = Model.objects.all()
    if u_fk:
        qs = qs.select_related(u_fk)
    qs = apply_common_filters(qs, Model, request)
    page_obj = paginate(request, qs)
    rows = rows_for_journal(page_obj.object_list)
    return render(request, "adminpanel/journal_list.html", {
        "section": "journal", "page_obj": page_obj, "rows": rows,
        "user_fk": u_fk, "q": request.GET.get('q', ''),
    })

# ============================
# Utilisateurs (avec compteurs)
# ============================
@staff_member_required
def users_list(request):
    """
    Liste des utilisateurs avec compteurs reliés (diagnostics, recos, images, health).
    Résistant aux noms de FK variables (user/patient/utilisateur/owner…).
    """
    qs = User.objects.all().order_by("username")

    def fk_to_user(Model):
        if not Model:
            return None
        # vrai FK vers auth.User
        for f in Model._meta.get_fields():
            rel = getattr(f, "remote_field", None)
            if rel and getattr(rel, "model", None) == User:
                return f.name
        # heuristique
        for name in ("user", "patient", "utilisateur", "owner"):
            if any(getattr(ff, "name", "") == name for ff in Model._meta.get_fields()):
                return name
        return None

    def count_subquery(Model, fk_name):
        """
        Annotation Subquery qui compte les lignes de Model pour chaque user courant.
        COALESCE(..., 0) pour afficher 0 plutôt que NULL.
        """
        if not (Model and fk_name):
            return Value(0, output_field=IntegerField())

        base = (
            Model.objects.filter(**{f"{fk_name}_id": OuterRef("pk")})
            .order_by()
            .values(fk_name)
            .annotate(c=Count("id"))
            .values("c")[:1]
        )
        return Coalesce(Subquery(base), Value(0), output_field=IntegerField())

    ann = {}
    # Diagnostics
    diag_fk = fk_to_user(globals().get("Diagnosis"))
    ann["diag_count"] = count_subquery(globals().get("Diagnosis"), diag_fk)

    # Recommendations
    reco_fk = fk_to_user(globals().get("Recommendation"))
    ann["reco_count"] = count_subquery(globals().get("Recommendation"), reco_fk)

    # Medical Images
    img_fk = fk_to_user(globals().get("MedicalImage"))
    ann["img_count"] = count_subquery(globals().get("MedicalImage"), img_fk)

    # Health data
    health_fk = fk_to_user(globals().get("HealthData"))
    ann["health_count"] = count_subquery(globals().get("HealthData"), health_fk)

    qs = qs.annotate(**ann)

    page_obj = paginate(request, qs, per_page=25)
    return render(request, "adminpanel/users_list.html", {
        "section": "users",
        "page_obj": page_obj,
    })
