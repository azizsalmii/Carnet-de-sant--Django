from django.urls import path
from . import views  # Cette ligne doit être présente !

urlpatterns = [
    path('', views.home, name='home'),
    path('journal/', views.journal_page, name='journal_page'),
    path('about/', views.about, name='about'),
    path('appointment/', views.appointment, name='appointment'),
    path('blog/', views.blog, name='blog'),
    path('blog/<int:pk>/', views.single_blog, name='single-blog'),
    path('contact/', views.contact, name='contact'),
    path('gallery/', views.gallery, name='gallery'),
    path('services/', views.service, name='services'),
    path('team/', views.team, name='team'),
    
    # URLs pour le système de rapports santé
    path('health-data/', views.health_data_list, name='health_data_list'),
    path('health-data/create/', views.health_data_create, name='health_data_create'),
    path('health-data/update/<int:pk>/', views.health_data_update, name='health_data_update'),
    path('health-data/delete/<int:pk>/', views.health_data_delete, name='health_data_delete'),
    
    path('reports/generate/', views.generate_monthly_report, name='generate_report'),
    path('reports/<int:pk>/', views.report_detail, name='report_detail'),
    path('reports/', views.report_list, name='report_list'),
    
    # URLs PDF
    path('reports/<int:pk>/pdf/', views.download_report_pdf, name='download_report_pdf'),
    path('reports/<int:pk>/view-pdf/', views.view_report_pdf, name='view_report_pdf'),
]