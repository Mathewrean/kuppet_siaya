from django import forms
from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html

from .models import (
    BECMember,
    BGCMember,
    BBFStatus,
    ContactMessage,
    FinancialStatement,
    GalleryAlbum,
    GalleryImage,
    NewsPost,
)


class GalleryImageInline(admin.TabularInline):
    model = GalleryImage
    extra = 1


@admin.register(GalleryAlbum)
class GalleryAlbumAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "slug",
        "category",
        "is_published",
        "show_on_homepage_slider",
        "slider_order",
        "slider_link",
    )
    list_filter = ("is_published", "show_on_homepage_slider", "category")
    search_fields = ("title", "slug", "description", "slider_caption", "category")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [GalleryImageInline]
    fieldsets = (
        (
            "Album Details",
            {
                "fields": (
                    "title",
                    "slug",
                    "category",
                    "description",
                    "cover_image",
                    "is_published",
                )
            },
        ),
        (
            "Homepage Slider",
            {
                "fields": (
                    "show_on_homepage_slider",
                    "slider_caption",
                    "slider_order",
                ),
                "description": "Enable an album for the homepage slider and control its caption and order.",
            },
        ),
    )

    class Media:
        js = ("core/admin/gallery_album_admin.js",)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "slider/",
                self.admin_site.admin_view(self.slider_management_view),
                name="core_gallery_slider_management",
            ),
        ]
        return custom_urls + urls

    def slider_link(self, obj):
        if not obj.show_on_homepage_slider:
            return "-"
        return format_html('<a href="{}">Manage Slider</a>', reverse("admin:core_gallery_slider_management"))

    slider_link.short_description = "Slider"

    def slider_management_view(self, request):
        if request.method == "POST":
            action = request.POST.get("action")
            if action == "add":
                album_id = request.POST.get("album_id")
                try:
                    album = GalleryAlbum.objects.get(pk=album_id, is_published=True)
                    album.show_on_homepage_slider = True
                    album.slider_order = GalleryAlbum.objects.filter(show_on_homepage_slider=True).count()
                    if not album.slider_caption:
                        album.slider_caption = album.title
                    album.save()
                    self.message_user(request, f"{album.title} added to the homepage slider.", level=messages.SUCCESS)
                except GalleryAlbum.DoesNotExist:
                    self.message_user(request, "Selected album could not be added.", level=messages.ERROR)
            elif action == "remove":
                album_id = request.POST.get("album_id")
                try:
                    album = GalleryAlbum.objects.get(pk=album_id)
                    album.show_on_homepage_slider = False
                    album.save(update_fields=["show_on_homepage_slider"])
                    self.message_user(request, f"{album.title} removed from the homepage slider.", level=messages.SUCCESS)
                except GalleryAlbum.DoesNotExist:
                    self.message_user(request, "Selected album could not be removed.", level=messages.ERROR)
            elif action == "save_order":
                ordered_ids = [value for value in request.POST.get("ordered_ids", "").split(",") if value]
                captions = {
                    key.replace("caption_", ""): value
                    for key, value in request.POST.items()
                    if key.startswith("caption_")
                }
                for position, album_id in enumerate(ordered_ids):
                    try:
                        album = GalleryAlbum.objects.get(pk=album_id)
                    except GalleryAlbum.DoesNotExist:
                        continue
                    album.slider_order = position
                    album.slider_caption = captions.get(album_id, "").strip()
                    album.save(update_fields=["slider_order", "slider_caption"])
                self.message_user(request, "Homepage slider order updated.", level=messages.SUCCESS)
            return HttpResponseRedirect(reverse("admin:core_gallery_slider_management"))

        slider_albums = GalleryAlbum.objects.filter(
            is_published=True,
            show_on_homepage_slider=True,
        ).order_by("slider_order", "title")
        available_albums = GalleryAlbum.objects.filter(is_published=True, show_on_homepage_slider=False).order_by("title")
        context = {
            **self.admin_site.each_context(request),
            "opts": self.model._meta,
            "title": "Homepage Slider Management",
            "slider_albums": slider_albums,
            "available_albums": available_albums,
        }
        return TemplateResponse(request, "admin/core/gallery_slider_management.html", context)


@admin.register(GalleryImage)
class GalleryImageAdmin(admin.ModelAdmin):
    list_display = ("album", "caption", "uploaded_at")
    list_filter = ("album",)
    search_fields = ("album__title", "caption")


@admin.register(NewsPost)
class NewsPostAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "is_published", "published_date")
    list_filter = ("is_published", "category")
    search_fields = ("title", "slug", "story")
    prepopulated_fields = {"slug": ("title",)}


admin.site.register(ContactMessage)
admin.site.register(BBFStatus)
admin.site.register(FinancialStatement)
admin.site.register(BECMember)
admin.site.register(BGCMember)
