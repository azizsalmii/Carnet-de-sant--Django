# projetPython/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from reco import views as reco_views
from django.http import HttpResponse
import os

def health(_request):
    return HttpResponse("ok")

def simple_home(_request):
    """Simple fallback home page to test if Django is working"""
    return HttpResponse("""
        <html>
        <head><title>Carnet de Santé</title></head>
        <body>
            <h1>✅ Django is Running!</h1>
            <p>Your deployment is successful.</p>
            <ul>
                <li><a href="/admin/">Admin Panel</a></li>
                <li><a href="/healthz">Health Check</a></li>
                <li><a href="/reco/dashboard/">Recommendations Dashboard</a></li>
                <li><a href="/users/login/">Login</a></li>
            </ul>
        </body>
        </html>
    """, content_type="text/html")

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # API routes (must be before other includes to avoid conflicts)
    path('api/recommendations/<int:reco_id>/provide_feedback/', reco_views.api_provide_feedback, name='api_provide_feedback'),
    path('api/metrics/run_recommendations/', reco_views.api_run_recommendations, name='api_run_recommendations'),
    path('api/', include('reco.api_urls')),            # ✅ API REST pour recommendations (DRF)

    # Apps principales
    path('', simple_home, name='home'),                # Simple fallback for testing
    path('journal/', include('journal.urls')),         # journal pages
    path('users/', include('users.urls')),             # gestion des utilisateurs
    path('accounts/', include('users.urls')),          # alias pour compatibilité Django
    path('reco/', include(('reco.urls', 'reco'), namespace='reco')),  # ✅ recommandations IA
    path('dashboard/', include(('adminpanel.urls', 'adminpanel'), namespace='adminpanel')),
    # Health check endpoint
    path('healthz/', health),
]

# Gate heavy ML routes behind env flag to avoid OOM on free tier
if os.getenv("ENABLE_AI_ROUTES", "0") == "1":
    urlpatterns += [
        path('ai/', include('ai_models.urls')),            # pages IA (chest-xray, brain-tumor)
        path('detection/', include('detection.urls')),     # détection d'anomalies (uses pandas/sklearn)
    ]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
