# ai_models/urls.py
from django.urls import path
from . import views  # <-- important



urlpatterns = [
    # Pages UI
    path('brain-tumor/', views.brain_tumor_test_page, name='brain_tumor_page'),
    path('chest-xray/', views.chest_xray_test_page, name='chest_xray_page'),

    # API prédiction
    path('api/chest-xray/', views.ChestXRayPredictView.as_view(), name='chest_xray_predict_api'),

    # Chat assistants
    path('api/brain-assistant/', views.brain_assistant_api, name='brain_assistant_api'),
    path('api/xray-assistant/', views.xray_assistant_api, name='xray_assistant_api'),

    # PDFs
    path('brain-tumor/report/', views.brain_report_pdf, name='brain_report_pdf'),
    path('diagnosis/<int:pk>/report/', views.diagnosis_report_pdf, name='diagnosis_report_pdf'),
]