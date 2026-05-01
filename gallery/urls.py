from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'admin/categories', views.AdminCategoryViewSet, basename='admin-categories')
router.register(r'admin/albums', views.AdminAlbumViewSet, basename='admin-albums')
router.register(r'admin/images', views.AdminImageViewSet, basename='admin-images')

urlpatterns = [
    # public API
    path('categories/', views.public_categories, name='gallery_public_categories'),
    path('albums/', views.public_albums, name='gallery_public_albums'),
    path('albums/<slug:slug>/', views.public_album_detail, name='gallery_public_album_detail'),
    path('homepage-slider/', views.homepage_slider, name='gallery_homepage_slider'),
    # admin API router
    path('', include(router.urls)),
]
