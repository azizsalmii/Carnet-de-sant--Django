# 🏥 Carnet de Santé - Django Health Tracking Platform

A comprehensive Django-based health management system integrating AI-powered medical diagnostics, personalized health recommendations, mental health support, and anomaly detection.

![Django](https://img.shields.io/badge/Django-5.2.7-green.svg)
![Python](https://img.shields.io/badge/Python-3.11-blue.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

---

## 🌟 Features

### 📊 Health Journal & Tracking
- **Daily Health Metrics**: Track blood pressure, heart rate, sleep quality, steps, and more
- **Mood Tracking**: Monitor emotional well-being with journal entries
- **Monthly Reports**: Automated PDF generation with health insights and visualizations
- **Historical Data**: Comprehensive timeline of health metrics

### 🤖 AI-Powered Medical Image Analysis
- **Chest X-Ray Analysis**: ResNet50-based detection of 14 conditions including:
  - Pneumonia, Cardiomegaly, Effusion, Infiltration
  - Mass, Nodule, Atelectasis, Pneumothorax
  - Pleural Thickening, Edema, Emphysema, Fibrosis
  - Consolidation, Hernia
- **Brain Tumor Classification**: ResNet18 model for tumor detection
- **Diagnostic Reports**: Automated PDF reports with medical advice
- **HTTPS Support**: Secure image upload and analysis

### 💡 Intelligent Health Recommendations
- **Rule-Based Engine**: 20+ medical rules for critical health conditions
- **ML Personalization**: Calibrated machine learning for relevance scoring
- **Feedback Learning**: Adaptive system that learns from user interactions
- **Multi-Category Insights**:
  - Sleep optimization
  - Blood pressure management
  - Activity & exercise guidance
  - Stress reduction
  - Nutrition advice
  - Emergency alerts

### 🧠 Mental Health Chatbot
- **Emotion Detection**: T5-based sentiment analysis
- **Therapeutic Techniques**:
  - Cognitive Behavioral Therapy (CBT)
  - Mindfulness exercises
  - Solution-focused responses
  - Crisis intervention
- **Context-Aware Conversations**: Maintains conversation history
- **Coping Strategies**: Personalized mental health resources

### 🔍 Health Anomaly Detection
- **Ensemble ML Models**: Isolation Forest + OneClassSVM
- **Composite Health Score**: 0-100 scoring across 4 domains:
  - Sleep quality (25%)
  - Physical activity (25%)
  - Cardiac health (25%)
  - Lifestyle factors (25%)
- **Smart Alerts**: Severity-based notifications (Critical, High, Medium, Low)
- **Visual Analytics**: Interactive dashboards with charts

### 🔐 User Management
- **Custom User Model**: Extended Django authentication
- **User Profiles**: Demographics, health goals, activity levels
- **Secure Authentication**: JWT token-based API access
- **Role-Based Access**: Admin panel for management

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- pip package manager
- Git

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/azizsalmii/Carnet-de-sant--Django.git
cd Carnet-de-sant--Django
```

2. **Create virtual environment:**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Apply migrations:**
```bash
python manage.py migrate
```

5. **Create superuser:**
```bash
python manage.py createsuperuser
```

6. **Run development server:**
```bash
python manage.py runserver
```

7. **Access the application:**
- Homepage: http://127.0.0.1:8000/
- Admin panel: http://127.0.0.1:8000/admin/
- API docs: http://127.0.0.1:8000/api/

---

## 🌐 Deployment Options

### Option 1: ngrok (Instant Local Testing)

**Perfect for demos, testing, and sharing your local app instantly!**

1. **Install ngrok:** https://ngrok.com/download

2. **Configure authtoken:**
```bash
ngrok config add-authtoken YOUR_TOKEN_HERE
```

3. **Start Django:**
```bash
# Set environment variable
set NGROK=true  # Windows
export NGROK=true  # Linux/Mac

python manage.py runserver 8080
```

4. **Start ngrok tunnel (new terminal):**
```bash
ngrok http 8080
```

5. **Access via public URL:** Copy the `https://xxxx.ngrok-free.app` URL from ngrok output.

**See [NGROK_QUICKSTART.md](NGROK_QUICKSTART.md) for detailed instructions.**

### Option 2: Render (Production)

1. **Create account:** https://render.com
2. **Connect GitHub repository**
3. **Configure `render.yaml`** (already included)
4. **Deploy!** Auto-deploys on git push

**See [render.yaml](render.yaml) for configuration details.**

### Option 3: PythonAnywhere

1. **Create account:** https://www.pythonanywhere.com
2. **Upload code via Git**
3. **Configure WSGI** (see [pythonanywhere_wsgi.py](pythonanywhere_wsgi.py))
4. **Set up virtual environment**

**See [QUICKSTART_PYTHONANYWHERE.md](QUICKSTART_PYTHONANYWHERE.md) for step-by-step guide.**

---

## 📁 Project Structure

```
Carnet-de-sant--Django/
├── ai_models/              # Medical image analysis (PyTorch models)
│   ├── views.py           # X-ray & brain tumor prediction
│   ├── assistant.py       # Medical advice templates
│   └── best_model.pth     # ResNet50 chest X-ray model
├── journal/               # Health tracking & journal
│   ├── models.py         # HealthData, JournalEntry, MonthlyReport
│   ├── views.py          # CRUD operations
│   └── services/         # PDF generation
├── reco/                  # AI recommendation engine
│   ├── engine.py         # Medical rules (20+ conditions)
│   ├── ml_service.py     # ML personalization
│   ├── feedback_learning.py  # Adaptive learning
│   └── models/v1/        # Trained ML models
├── detection/             # Anomaly detection system
│   ├── services/         # ML models (Isolation Forest, OneClassSVM)
│   └── views.py          # Health scoring & alerts
├── MentalHealth/          # Mental health chatbot
│   ├── views.py          # Emotion detection & therapy
│   └── ml_models/        # NLP models (vectorizer, classifier)
├── users/                 # User management
│   ├── models.py         # CustomUser, UserProfile
│   └── signals.py        # Auto-create profiles
├── projetPython/          # Django settings
│   ├── settings.py       # Configuration (multi-environment)
│   └── urls.py           # URL routing
├── templates/             # HTML templates
├── static/                # CSS, JS, images
├── media/                 # User uploads (avatars, diagnoses)
├── manage.py              # Django CLI
├── requirements.txt       # Python dependencies
├── requirements_ai.txt    # ML/AI dependencies
└── db.sqlite3            # SQLite database (development)
```

---

## 🛠️ Technology Stack

### Backend
- **Framework:** Django 5.2.7
- **Database:** SQLite (dev), PostgreSQL (production)
- **API:** Django REST Framework
- **Authentication:** JWT (Simple JWT)
- **Static Files:** WhiteNoise

### AI & Machine Learning
- **Deep Learning:** PyTorch 2.0+
- **Computer Vision:** torchvision, PIL
- **NLP:** Hugging Face Transformers (T5)
- **ML Models:** scikit-learn (Isolation Forest, OneClassSVM, Calibrated Classifier)
- **Data Processing:** pandas, numpy

### Frontend
- **HTML/CSS:** Bootstrap 5
- **JavaScript:** Vanilla JS + jQuery
- **Charts:** Chart.js
- **Icons:** Font Awesome

### Utilities
- **PDF Generation:** ReportLab
- **Image Processing:** Pillow
- **Environment Management:** python-decouple
- **Database URLs:** dj-database-url

---

## 📊 API Endpoints

### Health Recommendations
```
GET  /api/recommendations/personalized/     # ML-ranked recommendations
POST /api/recommendations/{id}/provide_feedback/  # Submit feedback
POST /api/metrics/run_recommendations/      # Generate recommendations
GET  /api/metrics/daily/                    # Daily health metrics
```

### Medical Image Analysis
```
POST /ai/chest-xray/analyze/               # Analyze chest X-ray
POST /ai/brain-tumor/analyze/              # Analyze brain MRI
GET  /ai/diagnoses/                        # User diagnosis history
```

### Mental Health
```
POST /mental/chat/                         # Chat with AI therapist
GET  /mental/history/                      # Conversation history
```

### Health Tracking
```
GET  /journal/health-data/                 # Health metrics
POST /journal/entries/                     # Create journal entry
GET  /journal/reports/monthly/             # Monthly PDF reports
```

---

## 🧪 Management Commands

### Seed Demo Data
```bash
python manage.py seed_demo --username testuser
```
Creates 7 days of sample health metrics for testing.

### Generate Recommendations
```bash
python manage.py genrecos --username testuser
```
Runs the recommendation engine for a specific user.

### Export Training Data
```bash
python manage.py export_training_data --output ./training_data
```
Exports recommendation feedback for ML model retraining.

---

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Django
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (optional, defaults to SQLite)
DATABASE_URL=postgresql://user:password@host:port/dbname

# Deployment Flags
RENDER=false
NGROK=false
PYTHONANYWHERE_DOMAIN=

# AI Models
ENABLE_HF_MODELS=1  # Set to 0 to disable Hugging Face models
IS_PRODUCTION=false
```

### Key Settings

**Development:**
- `DEBUG=True`
- SQLite database
- All AI models enabled
- Local static files

**Production:**
- `DEBUG=False`
- PostgreSQL database
- WhiteNoise for static files
- Dummy AI models (optional)
- HTTPS enforcement

---

## 📖 Documentation

- **[NGROK_SETUP.md](NGROK_SETUP.md)** - Complete ngrok deployment guide
- **[NGROK_QUICKSTART.md](NGROK_QUICKSTART.md)** - Quick reference for ngrok
- **[QUICKSTART_PYTHONANYWHERE.md](QUICKSTART_PYTHONANYWHERE.md)** - PythonAnywhere deployment
- **[AI_RECOMMENDATIONS_README.md](AI_RECOMMENDATIONS_README.md)** - Recommendation system docs
- **[MODEL_TRAINING_AND_FEEDBACK_GUIDE.md](MODEL_TRAINING_AND_FEEDBACK_GUIDE.md)** - ML model training
- **[FAQ_GOOGLE_COLAB.md](FAQ_GOOGLE_COLAB.md)** - Model training on Colab

---

## 🧑‍💻 Development

### Running Tests
```bash
# Test all apps
python manage.py test

# Test specific app
python manage.py test reco
python manage.py test ai_models
python manage.py test detection

# Run standalone test files
python test_ai_system.py
python test_reco_ai.py
```

### Code Quality
```bash
# Check for errors
python manage.py check

# View SQL migrations
python manage.py sqlmigrate reco 0001

# Database shell
python manage.py dbshell
```

### Creating New Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 🐛 Known Issues & Troubleshooting

### Port Already in Use
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID_NUMBER> /F

# Linux/Mac
lsof -ti:8000 | xargs kill -9
```

### Virtual Environment Issues
```bash
# Recreate venv
rm -rf venv
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### AI Model Loading Errors
- Models load lazily on first request (5-10s delay expected)
- Set `ENABLE_HF_MODELS=0` to disable heavy transformers
- Check `IS_PRODUCTION` flag for dummy models in production

### ngrok DisallowedHost Error
- Ensure `NGROK=true` environment variable is set
- Check `ALLOWED_HOSTS` includes `'*'` or `.ngrok-free.dev`
- Restart Django after settings changes

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👨‍💻 Author

**Aziz Salmi**
- GitHub: [@azizsalmii](https://github.com/azizsalmii)
- Project Link: [https://github.com/azizsalmii/Carnet-de-sant--Django](https://github.com/azizsalmii/Carnet-de-sant--Django)

---

## 🙏 Acknowledgments

- Django community for the excellent framework
- PyTorch team for deep learning tools
- Hugging Face for NLP models
- ngrok for instant deployment testing
- All contributors and testers

---

## 🚀 Quick Commands Cheat Sheet

```bash
# Setup
python -m venv venv && venv\Scripts\activate && pip install -r requirements.txt
python manage.py migrate && python manage.py createsuperuser

# Run (Development)
python manage.py runserver

# Run (ngrok)
set NGROK=true && python manage.py runserver 8080
# Then in new terminal: ngrok http 8080

# Testing
python manage.py test
python test_ai_system.py

# Utilities
python manage.py seed_demo --username testuser
python manage.py genrecos --username testuser
python manage.py collectstatic --noinput
```

---

## 📞 Support

If you encounter issues or have questions:
1. Check the [documentation](docs/) folder
2. Search existing [issues](https://github.com/azizsalmii/Carnet-de-sant--Django/issues)
3. Open a new issue with detailed information

---

**⭐ Star this repository if you find it useful!**

**Built with ❤️ using Django, PyTorch, and AI**
