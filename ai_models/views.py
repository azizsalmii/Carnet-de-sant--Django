# ai_models/views.py
# =========================================================
# Imports
# =========================================================
import io, base64, time, os, json
from PIL import Image
import torch
from torchvision import models, transforms

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated  # <-- AJOUT

from django.shortcuts import render
from django.core.files.storage import default_storage
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required        # <-- AJOUT

# ReportLab (⚠️ alias pour éviter conflit avec PIL.Image)
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Table, TableStyle            # <-- AJOUT


from .serializers import ChestXRayInputSerializer
from .assistant import get_bot_reply

from .models import Diagnosis   # <-- ajout
from django.core.files.base import ContentFile  # pour attacher le fichier si besoin
from django.shortcuts import get_object_or_404  # <-- en haut avec les imports

# =========================================================
# Device
# =========================================================
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


# =========================================================
# Chest X-Ray model + utils
# =========================================================
XRY_MODEL_PATH = r"C:\Users\IYED\Desktop\Carnet-de-sant--Django-main\ai_models\best_model.pth"

CONDITIONS = [
    'Atelectasis', 'Cardiomegaly', 'Consolidation', 'Edema',
    'Enlarged Cardiomediastinum', 'Fracture', 'Lung Lesion', 'Lung Opacity',
    'No Finding', 'Pleural Effusion', 'Pleural Other', 'Pneumonia',
    'Pneumothorax', 'Support Devices'
]

# Backbone ResNet50 multi-label
xray_model = models.resnet50(weights=None)
num_features = xray_model.fc.in_features
xray_model.fc = torch.nn.Linear(num_features, len(CONDITIONS))

# Charge le checkpoint
_xckpt = torch.load(XRY_MODEL_PATH, map_location=DEVICE)
if isinstance(_xckpt, dict):
    if "model_state_dict" in _xckpt:
        xray_model.load_state_dict(_xckpt["model_state_dict"], strict=False)
    elif "state_dict" in _xckpt:
        xray_model.load_state_dict(_xckpt["state_dict"], strict=False)
    else:
        xray_model.load_state_dict(_xckpt, strict=False)
else:
    xray_model = _xckpt

xray_model = xray_model.to(DEVICE).eval()


def preprocess_xray_image(input_data):
    """
    Supporte: UploadedFile, chemin fichier, base64 → retourne un tensor normalisé (1,3,224,224)
    """
    if hasattr(input_data, 'read'):
        img = Image.open(input_data).convert("RGB")
    elif isinstance(input_data, str) and os.path.exists(input_data):
        img = Image.open(input_data).convert("RGB")
    elif isinstance(input_data, str):
        try:
            img_bytes = base64.b64decode(input_data, validate=True)
            img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        except Exception as e:
            raise ValueError("Invalid base64 string or file path.") from e
    else:
        raise ValueError("Unsupported input type for image preprocessing.")

    tfs = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],
                             std=[0.229, 0.224, 0.225])
    ])
    return tfs(img).unsqueeze(0)


# =========================================================
# Utilitaire: sauvegarder un diagnostic en base (AJOUT)
# =========================================================
def _save_diagnosis(
    *, request, modality, predicted_class, probabilities, latency_ms,
    image_abs_path=None, summary=""
):
    """
    Crée un objet Diagnosis pour l'utilisateur connecté.
    - modality: Diagnosis.Modality.CXR ou Diagnosis.Modality.BRAIN
    - probabilities: dict {classe: proba}
    - image_abs_path: chemin ABSOLU du fichier uploadé (si dispo)
    """
    if not getattr(request, "user", None) or not request.user.is_authenticated:
        return None  # sécurité (les vues sont déjà protégées)

    # confiance = proba de la classe prédite si dispo
    conf = None
    try:
        conf = float(probabilities.get(predicted_class))
    except Exception:
        pass

    diag = Diagnosis(
        user=request.user,
        modality=modality,
        predicted_class=predicted_class,
        confidence=conf,
        probabilities=probabilities or {},
        latency_ms=float(latency_ms) if latency_ms is not None else None,
        summary=summary or "",
    )

    # Attacher le fichier d'origine si présent
    if image_abs_path and os.path.exists(image_abs_path):
        with open(image_abs_path, "rb") as f:
            filename = os.path.basename(image_abs_path)
            diag.image.save(filename, ContentFile(f.read()), save=False)

    diag.save()
    return diag


class ChestXRayPredictView(APIView):
    """POST /api/ai/chest-xray/"""
    permission_classes = [IsAuthenticated]  # <-- AJOUT : API protégée

    def post(self, request):
        serializer = ChestXRayInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            tensor = preprocess_xray_image(serializer.validated_data["image"])
            t0 = time.time()
            with torch.no_grad():
                output = xray_model(tensor.to(DEVICE))
                # Multi-label → sigmoid
                probs = torch.sigmoid(output)[0].cpu().numpy()
            latency = (time.time() - t0) * 1000.0
            predictions = {CONDITIONS[i]: float(probs[i]) for i in range(len(CONDITIONS))}
            top_condition, _ = sorted(predictions.items(), key=lambda x: x[1], reverse=True)[0]
            return Response({
                "predicted_class": top_condition,
                "probabilities": predictions,
                "latency_ms": round(latency, 2)
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@login_required(login_url='login')
def chest_xray_test_page(request):
    """Interface simple HTML Chest X-Ray (upload, prédiction, session, sauvegarde Diagnosis)."""
    result, image_url = None, None

    if request.method == "POST" and request.FILES.get("image"):
        file = request.FILES["image"]
        # Enregistrer l'image sous /media/diagnoses/...
        save_path = default_storage.save(f"diagnoses/{file.name}", file)
        abs_path = os.path.join(settings.MEDIA_ROOT, save_path)
        image_url = settings.MEDIA_URL + save_path

        try:
            tensor = preprocess_xray_image(abs_path)
            t0 = time.time()
            with torch.no_grad():
                output = xray_model(tensor.to(DEVICE))
                probs_t = torch.sigmoid(output)[0].cpu().numpy()

            latency = (time.time() - t0) * 1000.0
            predictions = {CONDITIONS[i]: float(probs_t[i]) for i in range(len(CONDITIONS))}
            top_condition, top_prob = sorted(predictions.items(), key=lambda x: x[1], reverse=True)[0]

            result = {
                "predicted_class": top_condition,
                "probabilities": predictions,
                "latency_ms": round(latency, 2),
            }

            # Session (chat / affichage)
            request.session["xray_predicted_class"] = top_condition
            request.session["xray_last_result"] = result
            request.session["xray_last_image"] = image_url

            # SAUVEGARDE EN BASE
            try:
                Diagnosis.objects.create(
                    user=request.user,
                    modality="cxr",
                    predicted_class=top_condition,
                    confidence=float(top_prob),              # 0..1
                    latency_ms=round(latency, 2),
                    summary="Chest X-Ray assistant result (non medical advice).",
                    probabilities=predictions,
                    image=save_path                           # chemin relatif
                )
            except Exception as db_err:
                print("[Diagnosis save xray] error:", db_err)

        except Exception as e:
            result = {"error": str(e)}

    return render(request, "ai_models/chest_xray.html", {"result": result, "image_url": image_url})


# =========================================================
# Brain Tumor model + utils
# =========================================================
BRAIN_MODEL_PATH = r"C:\Users\IYED\Desktop\Carnet-de-sant--Django-main\ai_models\resnet18_brain_tumor.pth"
BRAIN_CLASSES = ['Glioma', 'Meningioma', 'No_tumor', 'Pituitary']

# charge le modèle complet (même méthode que Flask)
brain_model = torch.load(BRAIN_MODEL_PATH, map_location=DEVICE, weights_only=False)
brain_model = brain_model.to(DEVICE).eval()

RESULT_DESCRIPTION = {
    "Glioma": "A glioma is a type of tumor that starts in the brain's glial cells...",
    "Meningioma": "A meningioma is usually non-cancerous...",
    "No_tumor": "Great news! No signs of a tumor were detected...",
    "Pituitary": "A pituitary tumor affects the pituitary gland...",
}
DEFAULT_SUMMARY = (
    "This result is model-generated and not a medical diagnosis. "
    "Please consult a qualified clinician for confirmation and next steps."
)
DISCLAIMER = (
    "This tool is not a medical device. Results may be inaccurate. "
    "Always consult a healthcare professional."
)


def preprocess_brain_image(path):
    img = Image.open(path).convert("RGB")
    tfs = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],
                             std=[0.229, 0.224, 0.225]),
    ])
    return tfs(img).unsqueeze(0)


@login_required(login_url='login')
def brain_tumor_test_page(request):
    """
    Upload MRI → prédiction.
    Stocke en session : brain_last_result, brain_last_image, brain_predicted_class (chat + export PDF).
    Sauvegarde aussi un objet Diagnosis en base.
    """
    result, image_url = None, None

    if request.method == "POST" and request.FILES.get("image"):
        file = request.FILES["image"]
        # Enregistrer l'image sous /media/diagnoses/...
        save_path = default_storage.save(f"diagnoses/{file.name}", file)
        abs_path = os.path.join(settings.MEDIA_ROOT, save_path)
        image_url = settings.MEDIA_URL + save_path

        try:
            x = preprocess_brain_image(abs_path).to(DEVICE)

            t0 = time.time()
            with torch.no_grad():
                out = brain_model(x)                 # logits
                pred_idx = int(out.argmax(1))
            latency = (time.time() - t0) * 1000.0

            pred_label = BRAIN_CLASSES[pred_idx]

            # Probabilités softmax
            probs = torch.softmax(out, dim=1)[0].cpu().tolist()
            prob_map = {BRAIN_CLASSES[i]: float(probs[i]) for i in range(len(BRAIN_CLASSES))}
            top_prob = max(probs)

            result = {
                "predicted_class": pred_label,
                "probabilities": prob_map,
                "description": RESULT_DESCRIPTION.get(pred_label, DEFAULT_SUMMARY),
                "disclaimer": DISCLAIMER,
                "latency_ms": round(latency, 2),
            }

            # Session pour PDF & chatbot
            request.session["brain_last_result"] = result
            request.session["brain_last_image"] = image_url
            request.session["brain_predicted_class"] = pred_label
            request.session.modified = True
            request.session.save()

            # SAUVEGARDE EN BASE
            try:
                Diagnosis.objects.create(
                    user=request.user,
                    modality="brain",
                    predicted_class=pred_label,
                    confidence=float(top_prob),          # 0..1
                    latency_ms=round(latency, 2),
                    summary=result["description"],
                    probabilities=prob_map, 
                    image=save_path                      # chemin relatif (géré par ImageField)
                )
            except Exception as db_err:
                print("[Diagnosis save brain] error:", db_err)

        except Exception as e:
            result = {"error": str(e)}
            request.session["brain_last_result"] = result
            request.session.modified = True
            request.session.save()

    return render(
        request,
        "ai_models/brain_tumor.html",
        {"result": result, "image_url": image_url, "mode": "brain"}
    )


# =========================================================
# Chatbot API (Brain)
# =========================================================
@login_required(login_url='login')            # <-- AJOUT : API JSON protégée
@require_POST
def brain_assistant_api(request):
    """
    API JSON: reçoit {message: str} et renvoie une réponse basée sur la classe prédite.
    La classe est lue depuis la session, définie dans brain_tumor_test_page().
    """
    try:
        data = json.loads(request.body.decode("utf-8"))
    except Exception:
        data = request.POST  # fallback form-encoded

    user_msg = (data.get("message") or "").strip()
    if not user_msg:
        return JsonResponse({"error": "Empty message"}, status=400)

    predicted = request.session.get("brain_predicted_class")  # ex: "Glioma"
    reply = get_bot_reply(user_msg, predicted)
    return JsonResponse({"ok": True, "reply": reply})


# =========================================================
# Export PDF (Brain)
# =========================================================
@login_required(login_url='login')            # <-- AJOUT : PDF protégé
def brain_report_pdf(request):
    """Génère un rapport PDF du dernier diagnostic (mémorisé en session)."""
    result = request.session.get("brain_last_result")
    image_url = request.session.get("brain_last_image")

    # Debug
    print("[brain_report_pdf] has result?", bool(result), "| has image?", bool(image_url))
    print("[brain_report_pdf] session keys:", list(request.session.keys()))

    if not result or "predicted_class" not in result:
        return HttpResponse("Aucun diagnostic disponible pour exporter le PDF.", status=400)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("<b>Rapport de Diagnostic — Détection de Tumeur Cérébrale</b>", styles["Title"]))
    story.append(Spacer(1, 20))

    story.append(Paragraph(f"<b>Résultat principal :</b> {result.get('predicted_class', '—')}", styles["Normal"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"<b>Temps d’analyse :</b> {result.get('latency_ms', 0)} ms", styles["Normal"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"<b>Description :</b> {result.get('description', '')}", styles["Normal"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"<b>Avertissement :</b> {result.get('disclaimer', '')}", styles["Normal"]))
    story.append(Spacer(1, 20))

    # Image (si disponible) → convertir URL /media/... en chemin disque
    if image_url:
        if image_url.startswith(settings.MEDIA_URL):
            rel = image_url[len(settings.MEDIA_URL):]   # "xxx.jpg" ou "uploads/xxx.jpg"
            image_path = os.path.join(settings.MEDIA_ROOT, rel)
        else:
            image_path = os.path.join(settings.BASE_DIR, image_url)

        if os.path.exists(image_path):
            story.append(RLImage(image_path, width=400, height=300))
            story.append(Spacer(1, 20))
        else:
            print("[brain_report_pdf] image file not found:", image_path)

    story.append(Paragraph("Généré automatiquement par le module IA Médicale – Carnet de Santé Global.", styles["Italic"]))

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    resp = HttpResponse(content_type="application/pdf")
    resp["Content-Disposition"] = 'attachment; filename="rapport_brain_tumor.pdf"'
    resp.write(pdf_bytes)
    return resp


@login_required(login_url='login')            # <-- AJOUT : API JSON protégée
@require_POST
def xray_assistant_api(request):
    """
    API JSON: {message: str} → réponse fondée sur la classe X-Ray mémorisée en session.
    """
    try:
        data = json.loads(request.body.decode("utf-8"))
    except Exception:
        data = request.POST

    user_msg = (data.get("message") or "").strip()
    if not user_msg:
        return JsonResponse({"error": "Empty message"}, status=400)

    predicted = request.session.get("xray_predicted_class")  # ex: "Pneumonia", "No Finding", etc.
    reply = get_bot_reply(user_msg, predicted, domain="xray")
    return JsonResponse({"ok": True, "reply": reply})

@login_required(login_url='login')
def diagnosis_report_pdf(request, pk):
    """
    Génère un PDF pour un diagnostic précis (par ID).
    Tolérant si le champ raw_probabilities n'existe pas ou est vide.
    """
    diag = get_object_or_404(Diagnosis, pk=pk, user=request.user)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    # Titre
    title = "Rapport de Diagnostic — Brain Tumor" if diag.modality == "brain" else "Rapport de Diagnostic — Chest X-Ray"
    story.append(Paragraph(f"<b>{title}</b>", styles["Title"]))
    story.append(Spacer(1, 16))

    # Infos principales
    story.append(Paragraph(f"<b>Utilisateur :</b> {request.user.username}", styles["Normal"]))
    story.append(Paragraph(f"<b>Date :</b> {diag.created_at.strftime('%d/%m/%Y %H:%M')}", styles["Normal"]))
    story.append(Paragraph(f"<b>Modality :</b> {diag.modality}", styles["Normal"]))
    story.append(Paragraph(f"<b>Résultat :</b> {diag.predicted_class}", styles["Normal"]))
    if diag.confidence is not None:
        story.append(Paragraph(f"<b>Confiance approx. :</b> {round(diag.confidence, 4)}", styles["Normal"]))
    if diag.latency_ms is not None:
        story.append(Paragraph(f"<b>Temps d’analyse :</b> {round(diag.latency_ms, 2)} ms", styles["Normal"]))
    story.append(Spacer(1, 12))

    # Résumé / description
    if diag.summary:
        story.append(Paragraph(f"<b>Résumé :</b> {diag.summary}", styles["Normal"]))
        story.append(Spacer(1, 12))

    # Probabilités (si disponibles)
    probs = getattr(diag, "raw_probabilities", None)
    # Si certaines anciennes lignes stockent une string JSON
    if isinstance(probs, str):
        try:
            probs = json.loads(probs)
        except Exception:
            probs = None

    if isinstance(probs, dict) and probs:
        data = [["Classe", "Probabilité"]]
        for k, v in sorted(probs.items(), key=lambda x: x[1], reverse=True):
            data.append([k, f"{float(v):.4f}"])
        tbl = Table(data, colWidths=[260, 120])
        tbl.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#e8f7f6")),
            ("TEXTCOLOR", (0,0), (-1,0), colors.HexColor("#0e2b3a")),
            ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#dce7ee")),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("ALIGN", (1,1), (-1,-1), "RIGHT"),
            ("BOTTOMPADDING", (0,0), (-1,0), 8),
            ("TOPPADDING", (0,0), (-1,0), 6),
        ]))
        story.append(Paragraph("<b>Détails des probabilités</b>", styles["Heading3"]))
        story.append(Spacer(1, 4))
        story.append(tbl)
        story.append(Spacer(1, 12))

    # Image si dispo
    if diag.image:
        try:
            # diag.image.path est dispo pour FileField/ImageField
            if os.path.exists(diag.image.path):
                story.append(Paragraph("<b>Image analysée</b>", styles["Heading3"]))
                story.append(Spacer(1, 6))
                story.append(RLImage(diag.image.path, width=400, height=300))
                story.append(Spacer(1, 12))
        except Exception as _img_err:
            print("[diagnosis_report_pdf] image error:", _img_err)

    # Disclaimer
    story.append(Paragraph(
        "Ce rapport est généré par un modèle IA et ne constitue pas un avis médical. "
        "Veuillez consulter un professionnel de santé.", styles["Italic"]
    ))

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    resp = HttpResponse(content_type="application/pdf")
    filename = f"diagnosis_{diag.id}_{diag.modality}.pdf"
    resp["Content-Disposition"] = f'attachment; filename="{filename}"'
    resp.write(pdf_bytes)
    return resp

