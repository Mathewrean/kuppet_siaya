from django.contrib import admin
from .models import GalleryCategory, GalleryAlbum, GalleryImage
from django.urls import path
from django.shortcuts import render
from django.contrib import admin as django_admin



@admin.register(GalleryCategory)
class GalleryCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_at')
    prepopulated_fields = {'slug': ('name',)}


class GalleryImageInline(admin.TabularInline):
    model = GalleryImage
    fields = ('image', 'title', 'order')
    extra = 0


@admin.register(GalleryAlbum)
class GalleryAlbumAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'is_published', 'show_on_homepage_slider', 'homepage_slider_order')
    list_filter = ('is_published', 'show_on_homepage_slider', 'category')
    inlines = [GalleryImageInline]
    search_fields = ('name', 'description')


@admin.register(GalleryImage)
class GalleryImageAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'album', 'order', 'uploaded_at')
    list_filter = ('album',)


# Add a custom admin view for slider management
def slider_management_view(request):
    # staff-only handled by admin_view wrapper when registering URL
    return render(request, 'admin/gallery/slider_management.html')


def categories_management_view(request):
    return render(request, 'admin/gallery/categories_management.html')


def albums_management_view(request):
    return render(request, 'admin/gallery/albums_management.html')


def album_manage_view(request, album_id):
    return render(request, 'admin/gallery/album_manage.html')


# append custom url to admin
original_get_urls = django_admin.site.get_urls

def get_urls():
    urls = original_get_urls()
    my_urls = [
        path('core/gallery/slider/', django_admin.site.admin_view(slider_management_view), name='core_gallery_slider_management'),
        path('core/gallery/categories/', django_admin.site.admin_view(categories_management_view), name='core_gallery_categories_management'),
        path('core/gallery/albums/', django_admin.site.admin_view(albums_management_view), name='core_gallery_albums_management'),
        path('core/gallery/albums/<int:album_id>/manage/', django_admin.site.admin_view(album_manage_view), name='core_gallery_album_manage'),
    ]
    return my_urls + urls

django_admin.site.get_urls = get_urls
from django.contrib import admin

# Register your models here.
