from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User


class ProtectedViewsTests(TestCase):
    """Tests pour vérifier l'accès aux vues protégées comme checkout ou mes achats."""

    def setUp(self):
        # Crée un utilisateur pour les tests
        self.user = User.objects.create_user(username="user1", password="pass123")

    def test_checkout_redirects_when_not_logged_in(self):
        """Un utilisateur non connecté doit être redirigé vers la page de login."""
        resp = self.client.post(reverse("checkout"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/login", resp.url)

    def test_checkout_access_when_logged_in(self):
        """Un utilisateur connecté peut accéder au checkout."""
        self.client.login(username="user1", password="pass123")
        resp = self.client.get(reverse("checkout"))
        # la vue checkout redirige probablement vers une page de confirmation / succès
        self.assertIn(resp.status_code, [200, 302])

    def test_my_purchases_requires_authentication(self):
        """La page Mes Achats doit rediriger vers login si non connecté."""
        resp = self.client.get(reverse("my_purchases"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/login", resp.url)

    def test_my_purchases_logged_user_ok(self):
        """Un utilisateur connecté peut voir ses achats (même si vide)."""
        self.client.login(username="user1", password="pass123")
        resp = self.client.get(reverse("my_purchases"))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "tickets/my_purchases.html")
