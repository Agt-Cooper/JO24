from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from tickets.models import Offer, Order, OrderItem

class CheckoutTests(TestCase):
    def setUp(self):
        self.client = Client()
        User = get_user_model()
        self.user = User.objects.create_user(
            username="u1",
            email="u1@example.com",
            password="pass1234"
        )

        if not hasattr(self.user, "profile"):
            from tickets.models import Profile
            Profile.objects.create(user=self.user, signup_key="TEST_SIGNUP_KEY")
        self.client.login(username="u1", password="pass1234")

        self.offer = Offer.objects.create(
            name="Natation",
            description="",
            price="25.00",
            offer_type="solo",
        )

    def test_checkout_creates_paid_order_and_ticket_and_clears_cart(self):
        #Met une offre dans le panier
        session = self.client.session
        session["cart"] = {str(self.offer.id): 2}
        session.save()

        #POST pour valider l’achat
        resp = self.client.post(reverse("checkout"))
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, reverse("my_purchases"))

        #Vérifie qu’une commande payée a été créée
        self.assertEqual(Order.objects.count(), 1)
        order = Order.objects.first()
        self.assertEqual(order.user, self.user)
        self.assertEqual(order.status, "paid")

        #Vérification si OrderItem créé avec clé finale + QR
        self.assertEqual(order.items.count(), 1)
        it: OrderItem = order.items.first()
        self.assertEqual(it.offer, self.offer)
        self.assertEqual(it.quantity, 2)
        self.assertTrue(it.final_key())
        self.assertTrue(it.qr_data_uri().startswith("data:image/png;base64,"))

        #Vide le panier
        session = self.client.session
        self.assertEqual(session.get("cart"), {})
