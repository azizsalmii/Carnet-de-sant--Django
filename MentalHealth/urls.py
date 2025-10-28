# mental_health/urls.py
from django.urls import path
from . import views

# Namespace the app urls to make reversing robust from templates and other apps
app_name = 'mental'

urlpatterns = [
    path('predict_text/', views.predict_text, name='predict_text'),
    path('submit_quiz/', views.submit_quiz, name='submit_quiz'),
    path('chat_with_bot/', views.chat_with_bot, name='chat_with_bot'),
    path('entry/edit/', views.edit_entry, name='edit_entry'),
    path('entry/delete/', views.delete_entry, name='delete_entry'),
    path('clear_history/', views.clear_history, name='clear_history'),
]
