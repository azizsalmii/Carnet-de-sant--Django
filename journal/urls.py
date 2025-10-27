from django.urls import path
from .views import (
    home, journal_page, about, appointment, blog, contact, gallery, service, single_blog, team
)

urlpatterns = [
    path('', home, name='home'),  # Home page, mapped to 'index' as per template
    path('journal/', journal_page, name='journal_page'),  # Existing journal page
    path('about/', about, name='about'),  # About page
    path('appointment/', appointment, name='appointment'),  # Appointment page
    path('blog/', blog, name='blog'),  # Blog listing page
    path('blog/<int:pk>/', single_blog, name='single-blog'),  # Single blog post (using post ID)
    path('contact/', contact, name='contact'),  # Contact page
    path('gallery/', gallery, name='gallery'),  # Gallery page
    path('services/', service, name='services'),  # Service page (mapped to 'services' as per template)
    path('team/', team, name='team'),  # Team page
]