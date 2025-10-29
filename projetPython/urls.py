# projetPython/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Apps principales
    path('', include('journal.urls')),                 # site principal (home, about, etc.)
    path('users/', include('users.urls')),             # gestion des utilisateurs
    path('accounts/', include('users.urls')),          # alias pour compatibilité Django
    path('ai/', include('ai_models.urls')),            # pages IA (chest-xray, brain-tumor)
    path('detection/', include('detection.urls')),     # détection d’anomalies
    path('reco/', include(('reco.urls', 'reco'), namespace='reco')),  # ✅ recommandations IA
    path('dashboard/', include(('adminpanel.urls', 'adminpanel'), namespace='adminpanel')),


path("mental/", include(("MentalHealth.urls", "mental"), namespace="mental"))

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
