from django.urls import path
from .views import register_page, home, login_page

urlpatterns = [
    path('', home, name='home'),             # page d'accueil
    path('register/', register_page, name='register_page'),  # page inscription
        path('login/', login_page, name='login_page'),

]
