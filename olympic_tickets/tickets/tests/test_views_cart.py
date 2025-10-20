from django.test import TestCase
from django.urls import reverse
from tickets.models import Offer

class CartViewsTests(TestCase):
    def setUp(self):
        self.offer = Offer.objects.create(
            name="Solo",
            offer_type="solo",
            price="19.90",
            description="1 personne"
        )

    def test_add_to_cart_creates_session_cart(self):
        url = reverse("add_to_cart", args=[self.offer.id])
        resp = self.client.get(url, follow=True)
        self.assertEqual(resp.status_code, 200)
        cart = self.client.session.get("cart")
        self.assertTrue(cart is not None)
        # selon implémentation: dict {offer_id: qty} ou liste d'IDs
        if isinstance(cart, dict):
            # clés peuvent être int ou str selon ta view
            self.assertIn(self.offer.id, cart) or self.assertIn(str(self.offer.id), cart)
        else:
            self.assertIn(self.offer.id, cart)