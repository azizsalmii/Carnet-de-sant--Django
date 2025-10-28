# ai_models/urls.py
from django.urls import path
from .views import (
    brain_tumor_test_page,
    chest_xray_test_page,
    ChestXRayPredictView,
    brain_assistant_api,
       brain_report_pdf, 
         xray_assistant_api,
         diagnosis_report_pdf, 
)

urlpatterns = [
    # Pages UI
    path('ai/brain-tumor/', brain_tumor_test_page, name='brain_tumor_page'),
    path('ai/chest-xray/', chest_xray_test_page, name='chest_xray_page'),

    # API prédiction
    path('api/ai/chest-xray/', ChestXRayPredictView.as_view(), name='chest_xray_predict_api'),

    # Chat assistants
    path('api/ai/brain-assistant/', brain_assistant_api, name='brain_assistant_api'),
    path('api/ai/xray-assistant/', xray_assistant_api, name='xray_assistant_api'),

    # PDF brain (tu l’as déjà)
    path('ai/brain-tumor/report/', brain_report_pdf, name='brain_report_pdf'),
        path('ai/diagnosis/<int:pk>/report/', diagnosis_report_pdf, name='diagnosis_report_pdf'),  # <-- AJOUT

        

]