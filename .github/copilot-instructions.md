# Copilot Instructions for Carnet-de-santé-Django

A comprehensive Django health tracking platform integrating AI-powered medical image analysis, personalized health recommendations, anomaly detection, and mental health support.

## Architecture Overview

**Multi-App Django Project** (`projetPython/settings.py` defines core config):
- **`users/`** — Custom user model (`CustomUser`) with `UserProfile` (demographics, blood group, avatar). Signals auto-create profiles on user registration.
- **`journal/`** — Health journal with mood tracking (`JournalEntry`), daily health metrics (`HealthData`), and automated monthly reports (`MonthlyReport`). PDF generation via `services/pdf_generator.py`.
- **`reco/`** — AI-powered recommendation engine combining rule-based logic (`engine.py`) with optional ML personalization (`ml_service.py`, `models/v1/*.joblib`). Includes feedback learning system.
- **`ai_models/`** — Medical image analysis: ResNet50 for chest X-rays (14 conditions), ResNet18 for brain tumor classification. PyTorch models loaded via `@lru_cache` in `views.py`. PDF diagnostic reports via ReportLab.
- **`detection/`** — Health anomaly detection system using Isolation Forest + OneClassSVM ensemble (`services/health_detector.py`). Calculates composite health scores (0-100) from sleep, activity, cardiac, and lifestyle metrics.
- **`MentalHealth/`** — Mental health chatbot with emotion classification (T5-based Hugging Face pipelines). Singleton `ModelManager` for optimized model loading.
- **`adminpanel/`** — Custom admin dashboard (not using Django admin).

**Data Storage:** SQLite (`db.sqlite3`), media files in `media/` (user avatars, diagnostic images).

## Critical Patterns & Conventions

### User Model Architecture
- **Auth user:** `settings.AUTH_USER_MODEL = 'users.CustomUser'` (required for all ForeignKeys to users).
- **Profiles:** Both `users.UserProfile` (demographics) AND `reco.Profile` (health goals, activity level) exist. They serve different purposes—maintain both when adding user features.
- **Signal coordination:** `users/signals.py` creates `UserProfile`, `reco/signals.py` creates `reco.Profile` on user save. Check both if modifying user creation flow.

### ML Model Loading Patterns
1. **Singleton pattern for heavy models:** Use `@lru_cache(maxsize=1)` (ai_models) or singleton classes (MentalHealth's `ModelManager`, reco's `get_personalization_service()`). Never instantiate directly in views to avoid repeated loading.
2. **Model file locations:**
   - Brain/CXR models: `ai_models/resnet18_brain_tumor.pth`, `ai_models/best_model.pth` (defined as `AI_BRAIN_CKPT`, `AI_CXR_CKPT` in settings)
   - Reco models: `models/v1/model_calibrated.joblib` (preferred) or `model.joblib`
   - Detection models: `detection/services/` has pkl files, journal has `ml/` directory with joblib files
3. **Device management:** Always use `DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")` and `.to(DEVICE)` for PyTorch models.

### Recommendation System Contract (reco/)
- **Rule functions:** Return `{'category': str, 'text': str, 'score': float}` or `None`. Order in `engine.rules()` defines priority (critical rules first, e.g., BP crisis).
- **Confidence conversion:** ML predictions are 0.0–1.0; `services.generate_recommendations_for_user()` multiplies by 100 for storage/thresholding. Keep conversions consistent in tests.
- **Deduplication:** Recommendations with identical text are skipped. Mind this when generating variations.
- **Feedback loop:** `feedback_learning.py` provides `get_personalized_confidence()` and `get_feedback_insights()` to boost/penalize categories based on user reactions.

### URL Namespacing
Always use namespaced URLs in templates/redirects:
```python
# In urls: path('reco/', include(('reco.urls', 'reco'), namespace='reco'))
# In templates: {% url 'reco:dashboard' %}
# In code: reverse('reco:personalized_recommendations')
```
Namespaces: `reco`, `reco_api`, `adminpanel`, `mental` (see `projetPython/urls.py`).

### Detection Health Score Calculation
Composite score from 4 domains (25% each): sleep, activity, cardiac, lifestyle. Values clamped 0-100. Categories: Poor (<50), Fair (50-70), Good (70-85), Excellent (85-100). See `detection/services/health_detector.py:DataPreprocessor.calculate_health_score()`.

## Key Entry Points & Workflows

### Recommendation Generation Pipeline
```python
# Full pipeline (typically triggered by DRF action or management command):
from reco.services import compute_features_for_user, generate_recommendations_for_user
features = compute_features_for_user(user.id)  # Aggregates DailyMetrics
generate_recommendations_for_user(user.id, features)  # Rules → ML filter → bulk_create

# Access ML service:
from reco.ml_service import get_personalization_service
ml = get_personalization_service()
confidence = ml.predict_helpfulness(user, 'sleep')
```

**CLI Commands:**
```bash
python manage.py seed_demo --username testuser     # Create 7 days sample metrics
python manage.py genrecos --username testuser      # Generate recommendations
python manage.py export_training_data --output ./training_data
```

**API Endpoints:**
- `POST /api/metrics/run_recommendations/` — Trigger generation for current user
- `GET /api/recommendations/personalized/` — ML-ranked recommendations with explanations
- `POST /api/recommendations/{id}/provide_feedback/` — Submit helpful/unhelpful feedback

### Medical Image Analysis
```python
# Chest X-ray prediction (ai_models/views.py):
model = get_xray_model()  # Cached ResNet50
tensor = preprocess_xray_image(uploaded_file)  # Returns (1,3,224,224) normalized tensor
predictions = model(tensor).sigmoid()  # 14-class multi-label output
results = {CONDITIONS[i]: float(predictions[0][i]) for i in range(len(CONDITIONS))}

# Brain tumor prediction:
model = get_brain_model()  # Cached ResNet18
probs = F.softmax(model(tensor), dim=1)
```
Models expect RGB images normalized to ImageNet stats. Always use provided `preprocess_*_image()` functions.

### Anomaly Detection Workflow
```python
# detection/views.py:analyze_user_data
preprocessor = DataPreprocessor()
df = preprocessor.calculate_health_score(df)      # Add composite score
features = preprocessor.prepare_features(df)      # Scale features
detector = IntelligentAnomalyDetector()
detector.detect_anomalies(features)               # Run ensemble (IF + OneClassSVM)
df = detector.ensemble_detection(df)              # Add anomaly flags
alert_system = HealthAlertSystem(df)
alerts_df = alert_system.generate_alerts()        # Generate severity-based alerts
```

## Development Commands

**Setup:**
```bash
pip install -r requirements.txt           # Core Django deps
pip install -r requirements_ai.txt        # ML/AI dependencies for reco app
python manage.py migrate                  # Apply all migrations
python manage.py createsuperuser          # Create admin user
```

**Running:**
```bash
python manage.py runserver                # Dev server at localhost:8000
```

**Testing:**
```bash
python manage.py test reco                # Reco app tests (models, engine, services, API)
python manage.py test ai_models           # AI models tests
python manage.py test detection           # Detection tests
# Root-level test files (test_*.py) are standalone integration tests
```

**DB Management:**
```bash
python manage.py makemigrations <app>     # Create migrations
python manage.py sqlmigrate <app> <num>   # View SQL for migration
python manage.py dbshell                  # Open SQLite shell
```

## Integration Points & Cross-Component Hooks

1. **Signals:** 
   - `users/signals.py`: Creates `UserProfile` on user creation
   - `reco/signals.py`: Creates `reco.Profile` on user creation (demo data disabled by default)
   - Check both when modifying user registration flow

2. **Shared User Data:**
   - `journal.HealthData` and `reco.DailyMetrics` store overlapping metrics (sleep, BP, steps). They serve different apps—journal for history, reco for AI. Don't consolidate without careful migration.
   - `users.CustomUser.age/poids/taille` duplicates some `UserProfile` fields—legacy issue, prefer `UserProfile`.

3. **Model Loading Timing:**
   - MentalHealth models load on first request via singleton—expect 2-5s delay on first chatbot use
   - Reco ML service loads on-demand via `get_personalization_service()`—gracefully degrades to rule-only if models missing
   - AI models (brain/CXR) load on first prediction via `@lru_cache`

4. **Static/Media Files:**
   - `detection/static/` and `reco/static/` have app-specific assets
   - `STATICFILES_DIRS` points to `detection/static/` only (legacy)—add other app statics if needed
   - Media uploaded to `media/avatars/`, `media/diagnoses/`, `media/diagnostics/`

## Common Editing Scenarios

**Adding a new health recommendation rule:**
1. Add rule function to `reco/engine.py` following contract (return dict or None)
2. Add to `rules()` list in desired priority order
3. Add rule variations to `reco/rule_variations.py` if using ML service
4. Update tests in `reco/tests.py` (EngineTests class)

**Modifying health score calculation:**
- Edit `detection/services/health_detector.py:DataPreprocessor.calculate_health_score()`
- Update feature columns in `select_features()` if changing inputs
- Retrain anomaly detection models: run analysis page to generate new models

**Adding new medical condition to X-ray classifier:**
- Update `CONDITIONS` list in `ai_models/views.py`
- Retrain ResNet50 model (external process)
- Replace `ai_models/best_model.pth` with new checkpoint
- Update `BRAIN_ADVICE` or CXR advice dicts in `ai_models/assistant.py`

**Changing ML model format:**
- Update `reco/ml_service.py:PersonalizationService._load_model()` to handle new format
- Maintain backward compatibility with existing `model_calibrated.joblib` / `model.joblib` files
- Update training scripts (if any) to match new format

## Important Files Reference

| File | Purpose | When to Edit |
|------|---------|-------------|
| `projetPython/settings.py` | Global config, installed apps, model paths | Adding apps, changing AI model locations |
| `projetPython/urls.py` | Root URL routing with namespaces | Adding new app routes |
| `users/models.py` | User, UserProfile (demographics) | User fields, auth changes |
| `reco/models.py` | Profile, DailyMetrics, Recommendation | Reco data schema changes |
| `reco/engine.py` | Rule definitions for recommendations | Adding/modifying health rules |
| `reco/services.py` | Recommendation generation pipeline | Changing generation logic, ML integration |
| `reco/ml_service.py` | ML personalization singleton | Model loading, prediction logic |
| `ai_models/views.py` | X-ray & brain tumor prediction endpoints | Image analysis logic, model loading |
| `ai_models/assistant.py` | Medical advice templates per condition | Diagnostic guidance content |
| `detection/services/health_detector.py` | Anomaly detection, health scoring | Detection algorithms, scoring formula |
| `MentalHealth/views.py` | Mental health chatbot, emotion analysis | Chatbot responses, NLP models |
| `journal/services/pdf_generator.py` | Health report PDF generation | Report formatting, content |

## Gotchas & Known Issues

- **Multiple Profile models:** `users.UserProfile` vs `reco.Profile`—both are active, don't confuse them.
- **Demo data disabled:** `reco/signals.py` no longer auto-creates `DailyMetrics` for new users (see comments in file to re-enable for testing).
- **Missing root test scripts:** References to `evaluate_ai_model.py`, `test_frontend.py` in docs but files don't exist—test files at root (e.g., `test_ai_system.py`) are standalone, run directly with `python test_*.py`.
- **Anomaly detector training:** Detection models are trained on-the-fly if missing—first analysis request with no saved models will be slow (training on 1000 sample records).
- **Settings module:** `DJANGO_SETTINGS_MODULE='projetPython.settings'` (note: project folder name differs from expected Django convention).
- **Confidence units:** Reco ML outputs 0-1, stored as 0-100. Always check which unit context expects.

---

**For questions or clarifications on any section, ask specific questions about the architecture, workflows, or editing patterns you need expanded.**
