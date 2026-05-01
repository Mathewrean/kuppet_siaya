from django.contrib import admin
from .models import GalleryCategory, GalleryAlbum, GalleryImage


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
from django.contrib import admin

# Register your models here.
