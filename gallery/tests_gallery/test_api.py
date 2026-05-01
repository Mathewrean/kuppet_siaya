from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from gallery.models import GalleryCategory, GalleryAlbum, GalleryImage
from django.core.files.uploadedfile import SimpleUploadedFile


User = get_user_model()


class GalleryAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        # CustomUser requires tsc_number on creation; do not pass username
        self.admin = User.objects.create_superuser(tsc_number='ADMIN001', email='admin@example.com', password='pass')
        self.client.force_authenticate(self.admin)
        self.cat = GalleryCategory.objects.create(name='Events')

    def test_create_album_and_upload_image_and_slider(self):
        # create album
        resp = self.client.post('/api/gallery/admin/albums/', {'name': 'Test Album', 'category': self.cat.id, 'is_published': True}, format='json')
        self.assertEqual(resp.status_code, 201)
        album_id = resp.json().get('id')

        # upload an image (valid)
        img = SimpleUploadedFile('img.jpg', b'\x47\x49\x46\x38\x39\x61', content_type='image/jpeg')
        resp = self.client.post(f'/api/gallery/admin/albums/{album_id}/images/', {'images': img}, format='multipart')
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertTrue(len(data) == 1)
        img_id = data[0]['id']

        # set album on slider
        resp = self.client.patch(f'/api/gallery/admin/albums/{album_id}/', {'show_on_homepage_slider': True, 'homepage_slider_order': 0}, format='json')
        self.assertIn(resp.status_code, (200, 202))

        # homepage slider should list it
        self.client.force_authenticate(None)
        resp = self.client.get('/api/gallery/homepage-slider/')
        self.assertEqual(resp.status_code, 200)
        slides = resp.json()
        self.assertTrue(any(s['album_slug'] for s in slides))

    def test_upload_invalid_type_and_size(self):
        self.client.force_authenticate(self.admin)
        resp = self.client.post('/api/gallery/admin/albums/', {'name': 'Album 2', 'category': self.cat.id, 'is_published': True}, format='json')
        album_id = resp.json().get('id')
        # invalid type
        bad = SimpleUploadedFile('bad.txt', b'hello', content_type='text/plain')
        resp = self.client.post(f'/api/gallery/admin/albums/{album_id}/images/', {'images': bad}, format='multipart')
        self.assertEqual(resp.status_code, 400)
        # oversized file
        big = SimpleUploadedFile('big.jpg', b'a'* (6*1024*1024), content_type='image/jpeg')
        resp = self.client.post(f'/api/gallery/admin/albums/{album_id}/images/', {'images': big}, format='multipart')
        self.assertEqual(resp.status_code, 400)

    def test_slider_reorder(self):
        self.client.force_authenticate(self.admin)
        a1 = GalleryAlbum.objects.create(name='A1', category=self.cat, is_published=True, show_on_homepage_slider=True, homepage_slider_order=0)
        a2 = GalleryAlbum.objects.create(name='A2', category=self.cat, is_published=True, show_on_homepage_slider=True, homepage_slider_order=1)
        resp = self.client.post('/api/gallery/admin/albums/slider_reorder/', {'order': [a2.id, a1.id]}, format='json')
        self.assertEqual(resp.status_code, 200)
        a1.refresh_from_db()
        a2.refresh_from_db()
        self.assertEqual(a2.homepage_slider_order, 0)
        self.assertEqual(a1.homepage_slider_order, 1)
