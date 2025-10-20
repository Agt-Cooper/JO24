from django.test import TestCase
from django.urls import reverse
from django.core.cache import cache
from django.contrib.auth import get_user_model

User = get_user_model()

class SigninViewTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(username="bob", email="b@x.test", password="My$ecret123")
        self.url = reverse("signin")

    def test_signin_success_by_username(self):
        resp = self.client.post(self.url, {"username": "bob", "password": "My$ecret123"}, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.context["user"].is_authenticated)

    def test_signin_fail_then_rate_limited(self):
        for _ in range(5):
            self.client.post(self.url, {"username": "bob", "password": "wrong"})
        resp = self.client.post(self.url, {"username": "bob", "password": "wrong"})
        self.assertContains(resp, "Trop de tentatives", status_code=200)

    def test_next_url_is_sanitized(self):
        resp = self.client.post(self.url, {
            "username": "bob",
            "password": "My$ecret123",
            "next": "https://evil.com/phish"
        }, follow=False)
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse("home"), resp["Location"])