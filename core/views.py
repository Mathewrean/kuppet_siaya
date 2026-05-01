from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.http import JsonResponse
from django.views.decorators.http import require_GET

from .models import BECMember, BGCMember, ContactMessage, GalleryAlbum, NewsPost


NEWS_CATEGORIES = [
    "General",
    "BEC Updates",
    "BGC Updates",
    "BBF News",
    "BUS News",
    "Events",
]

PLACEHOLDER_NEWS = [
    {
        "title": "Branch Assembly Update And Member Briefing",
        "category": "General",
        "story": "This placeholder article demonstrates the appearance of official branch updates, including card spacing, metadata, and archive layout for testing the design system.",
        "published_date": "April 24, 2026",
    },
    {
        "title": "BEC Planning Session On Welfare Priorities",
        "category": "BEC Updates",
        "story": "Use this preview content to confirm the visual treatment of category badges, typography, and consistent card heights across the responsive news grid.",
        "published_date": "April 18, 2026",
    },
    {
        "title": "Upcoming Branch Programmes And Events Calendar",
        "category": "Events",
        "story": "This sample item helps verify the balance of imagery, excerpts, and calls to action when there is not yet enough live content in the database.",
        "published_date": "April 11, 2026",
    },
]

PLACEHOLDER_ALBUMS = [
    {
        "title": "Teachers Day Celebration",
        "description": "Sample album preview for visual testing of the gallery cards and hover treatment.",
        "image_count": 14,
    },
    {
        "title": "Branch Meeting Highlights",
        "description": "Placeholder gallery content to validate spacing, labels, and cover image overlays.",
        "image_count": 9,
    },
    {
        "title": "Community Outreach",
        "description": "Preview imagery placeholder used when albums have not yet been published.",
        "image_count": 11,
    },
]

PLACEHOLDER_GALLERY_IMAGES = [
    {"caption": "Branch activity preview image"},
    {"caption": "Member engagement preview image"},
    {"caption": "Programme documentation preview image"},
    {"caption": "Event coverage preview image"},
]


def home(request):
    news = NewsPost.objects.filter(is_published=True).order_by("-published_date")[:6]
    albums = GalleryAlbum.objects.filter(is_published=True).prefetch_related("images")[:5]
    context = {
        "news": news,
        "albums": albums,
        "placeholder_news": [] if news else PLACEHOLDER_NEWS,
    }
    return render(request, "core/home.html", context)


def about(request):
    return render(request, "core/about.html")


def about_profile(request):
    return render(request, "core/about_profile.html")


def about_bec(request):
    members = BECMember.objects.all().order_by('order')
    return render(request, "core/about_bec.html", {"members": members})


def about_bgc(request):
    members = BGCMember.objects.all().order_by('order')
    return render(request, "core/about_bgc.html", {"members": members})


def projects(request):
    return render(request, "core/projects.html")


def projects_bbf(request):
    return render(request, "core/projects_bbf.html")


def projects_bus(request):
    return render(request, "core/projects_bus.html")


def projects_center(request):
    return render(request, "core/projects_center.html")


def gallery(request):
    albums = GalleryAlbum.objects.filter(is_published=True).prefetch_related("images").all()
    return render(
        request,
        "core/gallery.html",
        {
            "albums": albums,
            "placeholder_albums": [] if albums else PLACEHOLDER_ALBUMS,
        },
    )


def gallery_album(request, slug):
    album = get_object_or_404(
        GalleryAlbum.objects.prefetch_related("images"),
        slug=slug,
        is_published=True,
    )
    images = album.images.all()
    return render(
        request,
        "core/gallery_album.html",
        {
            "album": album,
            "images": images,
            "placeholder_images": [] if images else PLACEHOLDER_GALLERY_IMAGES,
        },
    )


def news_detail(request, slug):
    post = get_object_or_404(NewsPost, slug=slug, is_published=True)
    return render(request, "core/news_detail.html", {"post": post})


def news_archive(request):
    posts = NewsPost.objects.filter(is_published=True).order_by("-published_date")
    paginator = Paginator(posts, 12)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    return render(request, "core/news_archive.html", {"page_obj": page_obj})


def contact(request):
    if request.method == "POST":
        # Handle form submission
        pass
    return render(request, "core/contact.html")


@require_GET
def homepage_slider_api(request):
    albums = GalleryAlbum.objects.filter(
        is_published=True,
        show_on_homepage_slider=True,
    ).exclude(
        cover_image=""
    ).exclude(
        cover_image__isnull=True
    ).order_by("slider_order", "title")
    data = [
        {
            "id": album.id,
            "album_name": album.title,
            "album_slug": album.slug,
            "cover_image_url": album.cover_image.url if album.cover_image else None,
            "slider_caption": album.effective_slider_caption,
            "slider_order": album.slider_order,
        }
        for album in albums
    ]
    return JsonResponse(data, safe=False)
