# users/urls.py
from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Auth basique
    path('login/', views.login_view, name='login'),            # /accounts/login/
    path('logout/', views.logout_view, name='logout'),         # /accounts/logout/
    path('signup/', views.signup_view, name='signup'),         # /accounts/signup/
    path('profile/', views.profile_view, name='profile'),      # /accounts/profile/

    # ----- Password reset (Forgot password) -----
    path(
        'password-reset/',
        auth_views.PasswordResetView.as_view(
            template_name='users/password_reset.html',
            email_template_name='users/password_reset_email.txt',      # crée ce fichier (texte)
            subject_template_name='users/password_reset_subject.txt',  # crée ce fichier (texte)
            success_url=reverse_lazy('password_reset_done'),
        ),
        name='password_reset',
    ),
    path(
        'password-reset/done/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='users/password_reset_done.html'
        ),
        name='password_reset_done',
    ),
    path(
        'reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='users/password_reset_confirm.html',
            success_url=reverse_lazy('password_reset_complete'),
        ),
        name='password_reset_confirm',
    ),
    path(
        'reset/done/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='users/password_reset_complete.html'
        ),
        name='password_reset_complete',
    ),

    # ----- Password change (optionnel, pour utilisateur connecté) -----
    path(
        'password-change/',
        auth_views.PasswordChangeView.as_view(
            template_name='users/password_change.html',
            success_url=reverse_lazy('password_change_done'),
        ),
        name='password_change',
    ),
    path(
        'password-change/done/',
        auth_views.PasswordChangeDoneView.as_view(
            template_name='users/password_change_done.html'
        ),
        name='password_change_done',
    ),
]
