from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAdminUser, AllowAny
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.shortcuts import get_object_or_404
from django.db import transaction

from .models import GalleryCategory, GalleryAlbum, GalleryImage
from .serializers import (
    GalleryCategorySerializer, GalleryAlbumListSerializer, GalleryAlbumDetailSerializer, GalleryImageSerializer
)


@api_view(['GET'])
def public_categories(request):
    cats = GalleryCategory.objects.filter(albums__is_published=True).distinct()
    serializer = GalleryCategorySerializer(cats, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def public_albums(request):
    qs = GalleryAlbum.objects.filter(is_published=True)
    category = request.GET.get('category')
    if category:
        qs = qs.filter(category__slug=category)
    serializer = GalleryAlbumListSerializer(qs, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def public_album_detail(request, slug):
    album = get_object_or_404(GalleryAlbum, slug=slug, is_published=True)
    serializer = GalleryAlbumDetailSerializer(album)
    return Response(serializer.data)


@api_view(['GET'])
def homepage_slider(request):
    albums = GalleryAlbum.objects.filter(is_published=True, show_on_homepage_slider=True).order_by('homepage_slider_order')
    data = []
    for a in albums:
        cover = a.cover_image.image.url if a.cover_image and a.cover_image.image else None
        if not cover:
            first = a.images.order_by('order','uploaded_at').first()
            cover = first.image.url if first else None
        data.append({
            'id': a.id,
            'album_name': a.name,
            'album_slug': a.slug,
            'cover_image_url': cover,
            'slider_caption': a.homepage_slider_caption or a.name,
            'slider_order': a.homepage_slider_order,
        })
    return Response(data)


class AdminCategoryViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    queryset = GalleryCategory.objects.all()
    serializer_class = GalleryCategorySerializer


class AdminAlbumViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    queryset = GalleryAlbum.objects.all()
    lookup_field = 'pk'
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_serializer_class(self):
        return GalleryAlbumDetailSerializer

    @action(detail=True, methods=['post'])
    def images(self, request, pk=None):
        album = self.get_object()
        files = request.FILES.getlist('images')
        created = []
        # validation
        allowed_types = ['image/jpeg', 'image/png', 'image/webp']
        max_size = 5 * 1024 * 1024
        base_index = album.images.count()
        for idx, f in enumerate(files):
            # basic validation using content_type and size
            ct = getattr(f, 'content_type', '')
            if ct not in allowed_types:
                return Response({'error': 'Invalid file type'}, status=status.HTTP_400_BAD_REQUEST)
            if f.size > max_size:
                return Response({'error': 'File too large'}, status=status.HTTP_400_BAD_REQUEST)
            img = GalleryImage(album=album, image=f, order=base_index + idx)
            img.save()
            created.append(img)
        serializer = GalleryImageSerializer(created, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def set_cover(self, request, pk=None):
        album = self.get_object()
        img_id = request.data.get('image_id')
        img = get_object_or_404(GalleryImage, pk=img_id, album=album)
        album.cover_image = img
        album.save()
        return Response({'ok': True})

    @action(detail=True, methods=['post'])
    def reorder(self, request, pk=None):
        album = self.get_object()
        order = request.data.get('order') or []
        if not isinstance(order, list):
            return Response({'error': 'Order must be a list of image ids'}, status=400)
        with transaction.atomic():
            for idx, img_id in enumerate(order):
                GalleryImage.objects.filter(pk=img_id, album=album).update(order=idx)
        return Response({'ok': True})

    @action(detail=False, methods=['post'])
    def slider_reorder(self, request):
        """Reorder albums that are on the homepage slider.
        Expects JSON: {"order": [album_id1, album_id2, ...]}
        """
        order = request.data.get('order') or []
        if not isinstance(order, list):
            return Response({'error': 'Order must be a list of album ids'}, status=400)
        with transaction.atomic():
            for idx, album_id in enumerate(order):
                GalleryAlbum.objects.filter(pk=album_id, show_on_homepage_slider=True).update(homepage_slider_order=idx)
        return Response({'ok': True})


class AdminImageViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    queryset = GalleryImage.objects.all()
    serializer_class = GalleryImageSerializer

    def destroy(self, request, *args, **kwargs):
        img = self.get_object()
        album = img.album
        result = super().destroy(request, *args, **kwargs)
        # promote cover if necessary
        if album.cover_image_id == img.pk:
            album.promote_cover_after_delete()
        return result
from django.shortcuts import render

# Create your views here.
