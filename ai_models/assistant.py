# ai_models/assistant.py
import re
from typing import Dict, List, Optional, TypedDict

# --- Message légal global ---
GENERAL_DISCLAIMER = (
    "Je ne remplace pas un avis médical. Pour toute décision, consulte un médecin "
    "ou un service d’urgences en cas de symptômes graves."
)

# -------------------------------
# 1) CONSEILS — BRAIN (comme avant)
# -------------------------------
BrainAdvice = Dict[str, Dict[str, List[str] | str]]

BRAIN_ADVICE: BrainAdvice = {
    "Glioma": {
        "explain": (
            "Un gliome est une tumeur issue des cellules gliales du cerveau. "
            "Les formes varient (grade, localisation). Un neurochirurgien et un neuro-oncologue "
            "sont les interlocuteurs habituels pour confirmer le diagnostic et définir la prise en charge."
        ),
        "next": [
            "Conserver l’imagerie (IRM d’origine) et le compte-rendu.",
            "Prendre RDV avec un neurologue/neuro-oncologue.",
            "Noter l’historique des symptômes (début, fréquence, facteurs aggravants).",
        ],
        "watch": [
            "Céphalées inhabituelles persistantes",
            "Crises convulsives",
            "Troubles neurologiques nouveaux (vision, parole, faiblesse, équilibre)",
        ],
    },
    "Meningioma": {
        "explain": (
            "Un méningiome se développe à partir des méninges. Souvent bénin et à croissance lente, "
            "mais son impact dépend de la taille et de la localisation."
        ),
        "next": [
            "Consulter un neurochirurgien pour discuter surveillance vs intervention.",
            "Apporter l’ensemble des IRM et CD au rendez-vous.",
        ],
        "watch": [
            "Maux de tête progressifs",
            "Troubles visuels ou auditifs",
            "Déficits neurologiques focaux",
        ],
    },
    "Pituitary": {
        "explain": (
            "Une tumeur hypophysaire affecte l’hypophyse et peut perturber des hormones. "
            "Souvent bénigne, une évaluation endocrinologique est utile."
        ),
        "next": [
            "Dosages hormonaux (prescrits par endocrinologue).",
            "Bilan ophtalmologique si troubles visuels.",
        ],
        "watch": [
            "Changements de vision",
            "Fatigue marquée, prise de poids inexpliquée, troubles des règles",
        ],
    },
    "No_tumor": {
        "explain": (
            "Aucune tumeur détectée par le modèle sur cette image. C’est rassurant, "
            "mais seule l’évaluation clinique et radiologique officielle fait foi."
        ),
        "next": [
            "Si des symptômes persistent, montrer l’imagerie à un médecin.",
            "Suivre les recommandations d’hygiène de vie (sommeil, hydratation, gestion du stress).",
        ],
        "watch": [
            "Symptômes qui s’aggravent ou nouveaux signes neurologiques",
        ],
    },
}

# ------------------------------------
# 2) CONSEILS — CHEST X-RAY (nouveau)
#    On regroupe des classes en thèmes
# ------------------------------------
XRayAdvice = Dict[str, Dict[str, List[str] | str]]

XRAY_ADVICE: XRayAdvice = {
    "No Finding": {
        "explain": (
            "Aucune anomalie thoracique évidente détectée par le modèle sur cette radiographie. "
            "Seul l’avis du radiologue et le contexte clinique font foi."
        ),
        "next": [
            "Si des symptômes persistent (dyspnée, douleur thoracique, fièvre), consulte un médecin.",
            "Conserver l’image et le compte-rendu radiologique si disponible.",
        ],
        "watch": [
            "Fièvre prolongée, essoufflement croissant, douleur thoracique, toux sanguinolente.",
        ],
    },
    "Pneumonia": {
        "explain": (
            "Le modèle suggère des opacités compatibles avec une pneumonie (infection pulmonaire). "
            "Le diagnostic se confirme cliniquement (fièvre, toux) et biologiquement."
        ),
        "next": [
            "Consulter pour confirmation et éventuelle antibiothérapie.",
            "Hydratation, repos, antipyrétiques si besoin (suivant avis médical).",
        ],
        "watch": [
            "Essoufflement important, saturation basse, aggravation de la fièvre, douleurs latérales.",
        ],
    },
    "Pneumothorax": {
        "explain": (
            "Suspicion de pneumothorax (présence d’air entre poumon et paroi thoracique). "
            "C’est potentiellement urgent selon l’importance."
        ),
        "next": [
            "Consulter rapidement / urgences si douleur thoracique brutale et dyspnée.",
            "Ne pas différer l’évaluation clinique.",
        ],
        "watch": [
            "Aggravation de l’essoufflement, douleur intense, malaise.",
        ],
    },
    "Pleural Effusion": {
        "explain": (
            "Présence de liquide dans l’espace pleural. L’étiologie est variée (infection, insuffisance cardiaque, etc.)."
        ),
        "next": [
            "Avis médical pour bilan (clinique + imagerie complémentaire).",
            "Surveillance des symptômes respiratoires.",
        ],
        "watch": [
            "Dyspnée croissante, fièvre persistante, douleurs thoraciques.",
        ],
    },
    "Fracture": {
        "explain": (
            "Aspect compatible avec une fracture costale/osseuse. La confirmation est radiologique et clinique."
        ),
        "next": [
            "Consultation pour prise en charge de la douleur et conseils.",
            "Éviter les efforts douloureux ; protéger la zone.",
        ],
        "watch": [
            "Douleurs intenses, difficultés respiratoires, signe de complication (pneumothorax).",
        ],
    },
    "Opacity/Consolidation": {
        "explain": (
            "Opacité / consolidation pulmonaire : peut évoquer infection, atélectasie ou autre cause."
        ),
        "next": [
            "Corréler aux signes cliniques (fièvre, toux).",
            "Suivi médical et, si besoin, imagerie de contrôle.",
        ],
        "watch": [
            "Fièvre persistante, aggravation de la toux et de la dyspnée.",
        ],
    },
    "Edema/Cardiomegaly": {
        "explain": (
            "Signes compatibles avec surcharge/œdème pulmonaire et/ou cardiomégalie."
        ),
        "next": [
            "Évaluation cardiologique (clinique, ECG, biologie).",
            "Suivi du poids, œdèmes des membres, dyspnée d’effort.",
        ],
        "watch": [
            "Aggravation de l’essoufflement, œdèmes importants, douleur thoracique.",
        ],
    },
    "Support Devices": {
        "explain": (
            "Dispositifs de support visibles (ex: sondes, cathéters, pacemaker)."
        ),
        "next": [
            "Vérifier la position correcte par un professionnel.",
            "Suivre les consignes de soins du dispositif.",
        ],
        "watch": [
            "Douleur, rougeur, fièvre autour d’un site d’insertion, dysfonction du dispositif.",
        ],
    },
}

# Normalisation d’une classe brute (CheXpert/CheXNet/Custom) vers une « catégorie » ci-dessus
def _normalize_xray_class(raw: str) -> str:
    r = (raw or "").strip()
    if not r:
        return "No Finding"
    # mappings simples
    m = r.lower()
    if "no finding" in m:
        return "No Finding"
    if "pneumothorax" in m:
        return "Pneumothorax"
    if "pneumonia" in m:
        return "Pneumonia"
    if "effusion" in m:
        return "Pleural Effusion"
    if "fracture" in m:
        return "Fracture"
    if "opacity" in m or "consolidation" in m or "lesion" in m:
        return "Opacity/Consolidation"
    if "edema" in m or "cardiomegaly" in m or "enlarged cardiomediastinum" in m:
        return "Edema/Cardiomegaly"
    if "support" in m or "device" in m:
        return "Support Devices"
    # fallback
    return "Opacity/Consolidation"

# -------------------------------------------
# 3) Mini base de connaissances GÉNÉRALE (FAQ)
# -------------------------------------------
Topic = Dict[str, List[str] | str]
KB_TOPICS: Dict[str, Topic] = {
    "emergency": {
        "keywords": ["urgence", "urgences", "grav", "convulsion", "paralys", "parésie", "coma", "perte de connaissance"],
        "text": "Si tu suspectes une urgence médicale, il faut agir sans attendre.",
        "bullets": [
            "Appelle immédiatement les urgences (112 / 15).",
            "Signes d’alerte : déficit brutal d’un côté, trouble soudain de la parole ou de la vision, "
            "maux de tête explosifs, convulsions, altération de conscience.",
        ],
        "suggestions": ["Signes d’alerte", "Qui contacter ?", "Que préparer pour l’hôpital ?"],
    },
    "rdv": {
        "keywords": ["rdv", "rendez", "consult", "prise de rendez", "médecin"],
        "text": "Pour prendre RDV, contacte ton médecin traitant ou le service concerné.",
        "bullets": [
            "Apporte l’imagerie et les comptes-rendus (papier + CD/clé).",
            "Liste les symptômes, traitements, allergies, antécédents.",
            "Prépare tes questions (prise en charge, délais, suivi).",
        ],
        "suggestions": ["Quels examens apporter ?", "Questions à poser", "Délais habituels"],
    },
    "imagerie": {
        "keywords": ["irm", "scanner", "imagerie", "radiologie", "spectroscopie", "contraste", "rayon"],
        "text": "L’imagerie (IRM/Scanner/Rayons X) guide le diagnostic et le suivi.",
        "bullets": [
            "Toujours comparer aux examens antérieurs.",
            "Demander l’explication des éléments clés du compte-rendu.",
            "Respecter les protocoles et délais fixés par le radiologue.",
        ],
        "suggestions": ["Avec ou sans contraste ?", "Fréquence des contrôles", "Préparation à l’examen"],
    },
    "sleep": {
        "keywords": ["dormir", "sommeil", "insomnie", "fatigue"],
        "text": "Un sommeil régulier améliore l’humeur, la cognition et l’immunité.",
        "bullets": [
            "Heures de coucher/lever stables.",
            "Limiter les écrans 60–90 min avant dodo.",
            "Chambre sombre, calme et fraîche.",
        ],
        "suggestions": ["Rituel du soir", "Sieste ou pas ?", "Applis utiles"],
    },
    "hydration": {
        "keywords": ["hydrat", "boire", "eau", "déshydr"],
        "text": "L’hydratation soutient la tension artérielle, la cognition et le transit.",
        "bullets": [
            "Vise 1.5–2 L/j (à adapter au climat et à l’activité).",
            "Augmente en cas de fièvre, sport, chaleur.",
            "Urines jaune pâle = hydratation correcte.",
        ],
        "suggestions": ["Combien d’eau ?", "Boissons à éviter", "Signes de déshydratation"],
    },
    "stress": {
        "keywords": ["stress", "anxi", "angoisse", "relax"],
        "text": "Gérer le stress aide à mieux supporter les symptômes et à dormir.",
        "bullets": [
            "Respiration lente 4-7-8, cohérence cardiaque.",
            "Activité physique douce régulière.",
            "Limiter caféine/écrans tardifs.",
        ],
        "suggestions": ["Exercices rapides", "Applications", "Routine quotidienne"],
    },
}

# ------------------------------
# 4) Intent detection (commun)
# ------------------------------
HELLO_PAT = re.compile(r"\b(bonjour|salut|coucou|hey|hello)\b", re.I)
EXPLAIN_PAT = re.compile(r"(c.?est quoi|expliq|what|meaning|info|défin|type)", re.I)
NEXT_PAT = re.compile(r"(prochain|rdv|faire|next|suite|trait|prise en charge|consult)", re.I)
WATCH_PAT = re.compile(r"(sympt|surveill|watch|urgenc|danger|quand consulter)", re.I)

def _match_topic(message: str) -> Optional[str]:
    m = message.lower()
    for key, topic in KB_TOPICS.items():
        for w in topic["keywords"]:  # type: ignore[index]
            if w in m:
                return key
    return None

def _intent(message: str) -> str:
    if HELLO_PAT.search(message): return "hello"
    if EXPLAIN_PAT.search(message): return "explain"
    if NEXT_PAT.search(message): return "next"
    if WATCH_PAT.search(message): return "watch"
    return "generic"

# ------------------------------
# 5) Réponse unifiée
# ------------------------------
class BotReply(TypedDict, total=False):
    text: str
    bullets: List[str]
    suggestions: List[str]
    disclaimer: str

def get_bot_reply(
    message: str,
    predicted_class: Optional[str],
    domain: str = "brain",   # <-- compatible avec ton appel domain="xray"
) -> BotReply:
    """
    Retourne une réponse structurée {text, bullets?, suggestions?, disclaimer}.
    - domain="brain" (défaut) utilise BRAIN_ADVICE
    - domain="xray" utilise XRAY_ADVICE avec normalisation de classe
    """
    message = (message or "").strip()

    # — Sélection de la table de conseils
    if domain.lower() == "xray":
        cls_key = _normalize_xray_class(predicted_class or "No Finding")
        advice_table = XRAY_ADVICE
    else:
        cls_key = predicted_class or "No_tumor"
        advice_table = BRAIN_ADVICE

    by_class = advice_table.get(cls_key) or next(iter(advice_table.values()))

    # Intent de haut niveau
    intent = _intent(message)

    # a) salutation
    if intent == "hello":
        text = ("Bonjour ! Je peux expliquer le résultat, proposer les prochaines étapes "
                "ou dire ce qu’il faut surveiller. Tu peux aussi poser des questions générales "
                "(RDV, imagerie, sommeil, hydratation, stress…).")
        return {
            "text": text,
            "suggestions": ["Expliquer le résultat", "Prochaines étapes", "Que surveiller ?"],
            "disclaimer": GENERAL_DISCLAIMER,
        }

    # b) sujets généraux (FAQ)
    topic = _match_topic(message)
    if topic:
        t = KB_TOPICS[topic]
        return {
            "text": t["text"],                         # type: ignore[index]
            "bullets": t.get("bullets", []),           # type: ignore[assignment]
            "suggestions": t.get("suggestions", []),   # type: ignore[assignment]
            "disclaimer": GENERAL_DISCLAIMER,
        }

    # c) intents liés au résultat
    if intent == "explain":
        return {
            "text": str(by_class.get("explain", "")),
            "suggestions": ["Prochaines étapes", "Que surveiller ?"],
            "disclaimer": GENERAL_DISCLAIMER,
        }
    if intent == "next":
        return {
            "text": "Prochaines étapes suggérées :",
            "bullets": list(by_class.get("next", [])),     # type: ignore[arg-type]
            "disclaimer": GENERAL_DISCLAIMER,
        }
    if intent == "watch":
        return {
            "text": "Points de vigilance :",
            "bullets": list(by_class.get("watch", [])),    # type: ignore[arg-type]
            "disclaimer": GENERAL_DISCLAIMER,
        }

    # d) fallback générique
    generic = (
        "Je peux expliquer le résultat, proposer les prochaines étapes, indiquer les signes à surveiller "
        "et répondre à des questions générales (RDV, imagerie, sommeil, hydratation, stress…). Que souhaites-tu ?"
    )
    return {
        "text": generic,
        "suggestions": ["Expliquer le résultat", "Prochaines étapes", "Que surveiller ?"],
        "disclaimer": GENERAL_DISCLAIMER,
    }
