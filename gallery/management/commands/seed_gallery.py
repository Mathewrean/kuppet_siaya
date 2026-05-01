from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.conf import settings
from django.db import transaction
import os

from gallery.models import GalleryCategory, GalleryAlbum, GalleryImage


class Command(BaseCommand):
    help = 'Seed the gallery with sample categories, albums and images (KUPPET placeholders)'

    def add_arguments(self, parser):
        parser.add_argument('--albums-per-cat', type=int, default=2)
        parser.add_argument('--images-per-album', type=int, default=3)

    def handle(self, *args, **options):
        albums_per_cat = options['albums_per_cat']
        images_per_album = options['images_per_album']

        # support both `theme/static/images/...` and `theme/static/theme/images/...`
        static_dir_candidates = [
            os.path.join(settings.BASE_DIR, 'theme', 'static', 'images', 'gallery_placeholders'),
            os.path.join(settings.BASE_DIR, 'theme', 'static', 'theme', 'images', 'gallery_placeholders'),
        ]
        static_dir = None
        for c in static_dir_candidates:
            if os.path.isdir(c):
                static_dir = c
                break
        if not static_dir:
            self.stdout.write(self.style.ERROR(f'Placeholder images not found. Checked: {static_dir_candidates}'))
            return

        placeholder_files = sorted([f for f in os.listdir(static_dir) if f.endswith('.svg')])
        if not placeholder_files:
            self.stdout.write(self.style.ERROR('No placeholder SVGs found.'))
            return

        created_albums = 0
        created_images = 0

        with transaction.atomic():
            cats = [
                ('KUPPET Events', 'Events and activities by KUPPET Siaya'),
                ('Training & Workshops', 'Teacher training sessions and workshops'),
                ('Community', 'Community outreach and meetings'),
            ]

            for ci, (cname, cdesc) in enumerate(cats, start=1):
                cat, _ = GalleryCategory.objects.get_or_create(name=cname)
                for a in range(1, albums_per_cat + 1):
                    album_name = f"{cname} Album {a}"
                    album = GalleryAlbum.objects.create(
                        category=cat,
                        name=album_name,
                        description=cdesc,
                        is_published=True,
                        show_on_homepage_slider=(a == 1),
                        homepage_slider_order=(ci * 10 + a) if (a == 1) else None,
                        homepage_slider_caption=f"{album_name} — KUPPET Siaya",
                    )
                    created_albums += 1

                    # create images
                    for i in range(images_per_album):
                        fname = placeholder_files[(i) % len(placeholder_files)]
                        path = os.path.join(static_dir, fname)
                        with open(path, 'rb') as fh:
                            content = ContentFile(fh.read(), name=f"{album.slug}-{i+1}-{fname}")
                            img = GalleryImage(album=album, title=f"{album.name} Image {i+1}")
                            img.image.save(content.name, content, save=True)
                            img.order = i
                            img.save()
                            created_images += 1

                    # set first image as cover if available
                    first = album.images.order_by('order').first()
                    if first:
                        album.cover_image = first
                        album.save()

        self.stdout.write(self.style.SUCCESS(f'Created {created_albums} albums and {created_images} images.'))