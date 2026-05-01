from rest_framework import serializers
from .models import GalleryCategory, GalleryAlbum, GalleryImage


class GalleryImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = GalleryImage
        fields = ['id', 'album', 'image', 'title', 'caption', 'alt_text', 'order', 'uploaded_at']


class GalleryAlbumListSerializer(serializers.ModelSerializer):
    cover_image_url = serializers.SerializerMethodField()
    image_count = serializers.IntegerField(source='images.count', read_only=True)
    category = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = GalleryAlbum
        fields = ['id', 'name', 'slug', 'description', 'cover_image_url', 'image_count', 'category', 'created_at']

    def get_cover_image_url(self, obj):
        if obj.cover_image and obj.cover_image.image:
            return obj.cover_image.image.url
        # fallback to first image
        first = obj.images.order_by('order', 'uploaded_at').first()
        return first.image.url if first else None


class GalleryAlbumDetailSerializer(serializers.ModelSerializer):
    images = GalleryImageSerializer(many=True, read_only=True)
    # allow writing by pk for category
    category = serializers.PrimaryKeyRelatedField(queryset=GalleryCategory.objects.all(), allow_null=True, required=False)

    class Meta:
        model = GalleryAlbum
        fields = ['id', 'name', 'slug', 'description', 'category', 'is_published', 'show_on_homepage_slider', 'homepage_slider_caption', 'homepage_slider_order', 'images']


class GalleryCategorySerializer(serializers.ModelSerializer):
    album_count = serializers.IntegerField(source='albums.count', read_only=True)

    class Meta:
        model = GalleryCategory
        fields = ['id', 'name', 'slug', 'created_at', 'album_count']
