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
        response = self.client.post(url, data={"quantity": 1}, follow=False)
        self.assertEqual(response.status_code, 302)
        cart = self.client.session.get("cart", {})
        self.assertIn(str(self.offer.id), cart)
        self.assertEqual(int(cart[str(self.offer.id)]), 1)