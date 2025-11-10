from django.test import TestCase
from django.urls import reverse

class PublicViewsTests(TestCase):
    def test_home_view_renders(self):
        resp = self.client.get(reverse("home"))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "tickets/home.html")

    def test_bundle_list_view_renders(self):
        resp = self.client.get(reverse("bundle_list"))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "tickets/bundle.html")