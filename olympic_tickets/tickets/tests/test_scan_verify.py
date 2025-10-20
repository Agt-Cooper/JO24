from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from decimal import Decimal

from tickets.models import Offer, Profile, Order, OrderItem, Ticket

User = get_user_model()

class VerifyTicketTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="verif", email="v@x.test", password="Pw123456!")
        Profile.objects.get_or_create(user=self.user)
        self.offer = Offer.objects.create(name="Duo", offer_type="duo", price=Decimal("39.90"), description="2p")

        self.client.login(username="verif", password="Pw123456!")
        s = self.client.session
        s["cart"] = {str(self.offer.id): 1}
        s.save()
        self.client.post(reverse("checkout"), data={"confirm": "1"}, follow=True)
        self.ticket = Ticket.objects.first()

    def test_verify_valid_final_key(self):
        url = reverse("verify_ticket")  # à implémenter
        # Le scanner pourra envoyer GET ?code=... ou POST {"code": ...}
        resp = self.client.get(url, {"code": self.ticket.final_key})
        self.assertEqual(resp.status_code, 200)
        # On suppose une réponse JSON {"valid": true, "order_id": ...}
        self.assertIn(b'"valid": true', resp.content)

    def test_verify_invalid_final_key(self):
        url = reverse("verify_ticket")
        resp = self.client.get(url, {"code": "cle_invalide"})
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'"valid": false', resp.content)
