import logging

from django.contrib import messages
from django.core.paginator import Paginator
from django.db import DatabaseError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.http import JsonResponse
from django.views.decorators.http import require_GET

from .bbf_contacts import get_bbf_contacts
from .models import BECMember, BGCMember, ContactMessage, NewsPost
try:
    from gallery.models import GalleryAlbum as GalleryAlbumModel
except Exception:
    from .models import GalleryAlbum as GalleryAlbumModel


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


logger = logging.getLogger(__name__)


def home(request):
    try:
        news = list(NewsPost.objects.filter(is_published=True).order_by("-published_date")[:6])
    except DatabaseError:
        logger.exception("Failed to load homepage news.")
        news = []

    context = {
        "news": news,
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
    return render(request, "core/projects_bbf.html", {"contact_list": get_bbf_contacts()})


def projects_bus(request):
    return render(request, "core/projects_bus.html")


def projects_center(request):
    return render(request, "core/projects_center.html")


def gallery(request):
    albums = GalleryAlbumModel.objects.filter(is_published=True).prefetch_related("images").all()
    for a in albums:
        if not hasattr(a, 'title'):
            a.title = getattr(a, 'name', None)
        if getattr(a, 'cover_image', None):
            try:
                a.cover_image = a.cover_image.image
            except Exception:
                pass
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
        GalleryAlbumModel.objects.prefetch_related("images"),
        slug=slug,
        is_published=True,
    )
    images = album.images.all()
    # compatibility for templates expecting album.title and album.category as string
    if not hasattr(album, 'title'):
        album.title = getattr(album, 'name', None)
    if getattr(album, 'category', None):
        try:
            album.category = album.category.name
        except Exception:
            pass
    if getattr(album, 'cover_image', None):
        try:
            album.cover_image = album.cover_image.image
        except Exception:
            pass
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
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        email = request.POST.get("email", "").strip()
        tsc_number = request.POST.get("tsc_number", "").strip()
        phone_number = request.POST.get("phone_number", "").strip()
        subject = request.POST.get("subject", "").strip()
        message_text = request.POST.get("message", "").strip()
        consent = request.POST.get("consent") == "on"

        ContactMessage.objects.create(
            first_name=first_name,
            last_name=last_name,
            email=email,
            tsc_number=tsc_number,
            phone_number=phone_number,
            subject=subject,
            message=message_text,
            consent=consent,
        )

        if request.headers.get("Accept") == "application/json" or request.headers.get(
            "X-Requested-With"
        ) == "XMLHttpRequest":
            return JsonResponse(
                {"success": True, "message": "Your message has been sent successfully!"}
            )

        messages.success(request, "Your message has been sent successfully!")
        return redirect("contact")

    return render(request, "core/contact.html")


@require_GET
def homepage_slider_api(request):
    try:
        albums = list(GalleryAlbumModel.objects.filter(
            is_published=True,
            show_on_homepage_slider=True,
        ).order_by('homepage_slider_order'))
    except DatabaseError:
        logger.exception("Failed to load homepage slider albums.")
        return JsonResponse([], safe=False)

    data = []
    for album in albums:
        cover = None
        if getattr(album, 'cover_image', None) and getattr(album.cover_image, 'image', None):
            cover = album.cover_image.image.url
        else:
            first = album.images.order_by('order', 'uploaded_at').first()
            cover = first.image.url if first else None
        data.append({
            'id': album.id,
            'album_name': getattr(album, 'name', None) or getattr(album, 'title', ''),
            'album_slug': album.slug,
            'cover_image_url': cover,
            'slider_caption': album.homepage_slider_caption or (getattr(album, 'name', None) or ''),
            'slider_order': album.homepage_slider_order,
        })
    return JsonResponse(data, safe=False)
