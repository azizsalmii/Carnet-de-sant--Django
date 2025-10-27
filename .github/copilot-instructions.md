## Copilot / AI agent instructions for Carnet-de-sant--Django

Purpose: help an AI coding agent be immediately productive in this repository by summarizing the architecture, developer workflows, and concrete code hotspots to edit or inspect.

- Big picture (what to change and why):
  - The `reco/` Django app implements an AI+rules recommendation system. It combines a pure rule engine (`reco/engine.py`) with an optional ML personalization layer (`reco/ml_service.py` and `models/v1/*.joblib`). Changes that affect recommendation behavior usually touch one or more of: feature computation (`reco/features.py`), rule variations (`reco/rule_variations.py`), service orchestration (`reco/services.py`), ML logic (`reco/ml_service.py`), or feedback learning (`reco/feedback_learning.py`).

- Key files and quick reads (start here):
  - `reco/engine.py` — rule functions; each rule returns a dict {category, text, score} or None. See `rules()` and its ordering (priority matters).
  - `reco/ml_service.py` — `PersonalizationService` / `get_personalization_service()` global instance. Model-loading logic (priority: `model_calibrated.joblib` then `model.joblib`) and feature -> prediction path live here.
  - `reco/features.py` — `FeatureEngineer` provides the canonical feature computations used for training and inference. Use this for any ML-related changes.
  - `reco/services.py` — orchestration: `compute_features_for_user()` and `generate_recommendations_for_user()` implement the full generation pipeline (delete old recos, run rules, call ML to filter/rank, bulk_create results).
  - `reco/api.py` — DRF ViewSets and custom actions (`run_recommendations`, `provide_feedback`, `personalized`). Use this for API surface changes.
  - `reco/management/commands/` — CLI workflows (e.g., `genrecos`, `seed_demo`, `export_training_data`, `import_public_data`). Edit here to change batch jobs.
  - `models/v1/` — trained artifacts. `model_calibrated.joblib` is preferred by code; `scaler.joblib` may also be present.

- Concrete dataflow summary (edit points):
  1. UI/clients post DailyMetrics (models in `reco/models.py`) or run management commands.
  2. `services.compute_features_for_user()` or `FeatureEngineer.compute_comprehensive_features()` computes features.
  3. `engine.rules()` produces candidate recommendations from features (rule-based).
  4. `ml_service.PersonalizationService` predicts helpfulness and ranks/filter results. If no model present, code falls back to rule-only behavior.
  5. `services.generate_recommendations_for_user()` applies ML boosts using `feedback_learning` insights, deduplicates by recommendation text, and bulk-creates `Recommendation` rows.

- Important conventions & gotchas (project-specific):
  - Rule contract: functions in `reco/engine.py` return recommendation dicts with keys 'category','text','score' or None. Order returned by `rules()` defines priority; critical rules are first (e.g., BP crisis).
  - ML model format: code expects either a calibrated model file `model_calibrated.joblib` or `model.joblib`. `model.joblib` may be a dict { 'model': ..., 'scaler': ... } or a raw model object. Always use `get_personalization_service()` rather than instantiating `PersonalizationService` directly to avoid repeated heavy model loads.
  - Confidence semantics: internal ML confidence is 0.0–1.0; `services.generate_recommendations_for_user()` multiplies by 100 when applying thresholding. Tests and logging often compare percent-style numbers—keep conversions consistent.
  - Deduplication: the code skips candidate recommendations whose exact text was seen before (text equality). If adjusting content generation, mind duplicates.
  - Feedback learning: feedback is consumed via `reco/feedback_learning.py` (functions like `get_personalized_confidence` and `get_feedback_insights`) — changing feedback schema requires updating generation & training code.

- Developer workflows & commands (how to run things locally):
  - Install AI deps: `pip install -r requirements_ai.txt` (this file at repo root contains the main packages used by `reco/`).
  - Add app to settings: ensure `'reco'` is in `INSTALLED_APPS` in `projetPython/settings.py` (the README shows required REST_FRAMEWORK settings).
  - Run migrations: `python manage.py makemigrations reco` and `python manage.py migrate`.
  - Create data / generate recos:
    - `python manage.py seed_demo --username <username>` (seed demo data)
    - `python manage.py genrecos --username <username>` (generate recommendations)
    - `python manage.py export_training_data --output ./training_data`
  - Run tests for the recommendations app: `python manage.py test reco` (tests focus on models, the rule engine, services, and API endpoints).
  - Run dev server: `python manage.py runserver` and use the following endpoints:
    - `GET /api/recommendations/personalized/` — ML-ranked recos with explanations
    - `POST /api/metrics/run_recommendations/` — trigger generation for current user

- Integration points & cross-component hooks to be aware of:
  - Signals: `reco/signals.py` may auto-trigger recommendation refresh on metric save—check it before altering generation timing.
  - API layer: DRF ViewSets are in `reco/api.py`; custom actions mirror management commands and should remain consistent with CLI behavior.
  - Templates & frontend: `reco/templates/reco/` and `reco/static/reco/` render cards and feedback buttons; changing recommendation fields shown (e.g., `ml_confidence`, `explanation`) requires template updates.
  - Model files: trained artifacts are stored under `models/v1/`. Updating model loading logic requires careful handling of the scaler and calibrated model fallback implemented in `ml_service._load_model()`.

- Quick examples to copy when editing code:
  - To get features + generate recos from code:
    from reco.services import compute_features_for_user, generate_recommendations_for_user
    features = compute_features_for_user(user.id)
    generate_recommendations_for_user(user.id, features)

  - To access the ML service singleton:
    from reco.ml_service import get_personalization_service
    ml = get_personalization_service()
    ml.predict_helpfulness(user, 'sleep')

- Notes & missing pieces discovered during inspection:
  - AI_RECOMMENDATIONS_README.md references helper scripts like `evaluate_ai_model.py` and `test_frontend.py` but those files aren't present in the repository root—verify with the team before relying on them.
  - Some production choices are opinionated (the pipeline deletes previous recommendations and bulk-creates new ones). If you need retention for analytics, update `services.generate_recommendations_for_user()` accordingly.

If any section above is unclear or you'd like the instructions expanded to include example PR templates, test edit workflows, or a short checklist for model updates (retraining -> file format -> deploy), tell me which area to expand and I'll iterate.
