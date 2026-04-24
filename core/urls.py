from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('about/profile/', views.about_profile, name='about_profile'),
    path('about/bec/', views.about_bec, name='about_bec'),
    path('about/bgc/', views.about_bgc, name='about_bgc'),
    path('projects/', views.projects, name='projects'),
    path('projects/bbf/', views.projects_bbf, name='projects_bbf'),
    path('projects/bus/', views.projects_bus, name='projects_bus'),
    path('projects/kuppet-center/', views.projects_center, name='projects_center'),
    path('gallery/', views.gallery, name='gallery'),
    path('gallery/<slug:slug>/', views.gallery_album, name='gallery_album'),
    path('contact/', views.contact, name='contact'),
    path('news/<slug:slug>/', views.news_detail, name='news_detail'),
    path('news/', views.news_archive, name='news_archive'),
]
