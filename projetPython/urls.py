from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('user/', include('users.urls')),  # Si vous avez des URLs spécifiques aux users
    
    # URLs d'authentification
    path('accounts/login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    
    # Vos URLs existantes
    path('', include('journal.urls')),  # Incluez les URLs du journal ici
]