from django.db import models
from django.utils.text import slugify
from django.utils import timezone


class GalleryCategory(models.Model):
    name = models.CharField(max_length=150, unique=True)
    slug = models.SlugField(max_length=160, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class GalleryAlbum(models.Model):
    category = models.ForeignKey(GalleryCategory, related_name='albums', on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.TextField(blank=True)
    cover_image = models.ForeignKey('GalleryImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    is_published = models.BooleanField(default=False)
    show_on_homepage_slider = models.BooleanField(default=False)
    homepage_slider_order = models.PositiveIntegerField(null=True, blank=True)
    homepage_slider_caption = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name)[:200]
            slug = base
            i = 1
            while GalleryAlbum.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{i}"
                i += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def promote_cover_after_delete(self):
        # Ensure cover image is valid; promote next image if needed
        if not self.cover_image:
            next_img = self.images.order_by('order', 'uploaded_at').first()
            if next_img:
                self.cover_image = next_img
                self.save()


class GalleryImage(models.Model):
    album = models.ForeignKey(GalleryAlbum, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='gallery_images/')
    title = models.CharField(max_length=200, blank=True)
    caption = models.TextField(blank=True)
    alt_text = models.CharField(max_length=255, blank=True)
    order = models.PositiveIntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'uploaded_at']

    def __str__(self):
        return f"{self.album.name} - {self.title or self.pk}"

    def save(self, *args, **kwargs):
        # if alt_text is empty, seed from title
        if not self.alt_text and self.title:
            self.alt_text = self.title
        super().save(*args, **kwargs)
from django.db import models

# Create your models here.
