from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from tickets.models import Offer, Order, OrderItem

user = get_user_model()


class PurchasesViewTests(TestCase):
    def setUp(self):
        self.user = user.objects.create_user(
            username="testuser",
            email="user@example.com",
            password="StrongPassw0rd!"
        )
        self.client.login(username="testuser", password="StrongPassw0rd!")

        self.offer = Offer.objects.create(
            name="Natation",
            offer_type="solo",
            price="50.00",
            description="Natation solo"
        )

    def test_my_purchases_empty(self):
        """
        Si aucune commande payée,
        utilisateur voit affiché "Aucun achat".
        """
        url = reverse("my_purchases")
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Aucun achat pour le moment")
        ctx = resp.context
        self.assertFalse(ctx["has_orders"])

    def test_my_purchases_with_paid_order_and_qr(self):
        """
        Si il existe une commande payée existe (avec des OrderItem)
        on doit voir la commande et le QR code généré.
        """
        # Crée une commande payée
        order = Order.objects.create(
            user=self.user,
            status="paid",
            purchase_key="FAKE_PURCHASE_KEY"
        )

        # Crée une ligne de commande
        item = OrderItem.objects.create(
            order=order,
            offer=self.offer,
            quantity=2,
            unit_price=self.offer.price,
        )

        url = reverse("my_purchases")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

        html = resp.content.decode("utf-8")

        # On voit bien l'offre
        self.assertIn("Natation", html)

        # Et un QR code sous forme de data URI
        self.assertIn("data:image/png;base64", html)

        ctx = resp.context
        self.assertTrue(ctx["has_orders"])
