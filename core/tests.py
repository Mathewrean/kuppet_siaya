from unittest.mock import patch

from django.db import DatabaseError
from django.test import TestCase


class HomepageResilienceTests(TestCase):
    def test_home_renders_placeholders_when_news_query_fails(self):
        with self.assertLogs("core.views", level="ERROR"), patch(
            "core.views.NewsPost.objects.filter",
            side_effect=DatabaseError("missing table"),
        ):
            response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Preview Story")

    def test_slider_api_returns_empty_list_when_gallery_query_fails(self):
        with self.assertLogs("core.views", level="ERROR"), patch(
            "core.views.GalleryAlbumModel.objects.filter",
            side_effect=DatabaseError("missing table"),
        ):
            response = self.client.get("/api/gallery/homepage-slider/")

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, [])
