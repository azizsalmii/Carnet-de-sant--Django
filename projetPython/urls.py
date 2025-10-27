# projetPython/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('user/', include('users.urls')),
    path('', include('journal.urls')),
    path('', include('ai_models.urls')),   # <- important
    path('accounts/', include('users.urls')),  # <--- AJOUT


 path('', include('detection.urls')),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
