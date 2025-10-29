# projetPython/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # Apps principales
    path('', include('journal.urls')),
    path('users/', include('users.urls')),
    path('accounts/', include('users.urls')),
    path('ai/', include('ai_models.urls')),
    path('detection/', include('detection.urls')),
    path('reco/', include(('reco.urls', 'reco'), namespace='reco')),
    path('dashboard/', include(('adminpanel.urls', 'adminpanel'), namespace='adminpanel')),
    path('mental/', include(('MentalHealth.urls', 'mental'), namespace='mental')),

    # ✅ API DRF pour reco (router)
    path('api/', include(('reco.api_urls', 'reco_api'), namespace='reco_api')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
