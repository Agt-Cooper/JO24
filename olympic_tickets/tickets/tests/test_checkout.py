from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.storage import default_storage
from django.conf import settings
from decimal import Decimal
import os, tempfile, shutil

from tickets.models import Offer, Profile, Order, OrderItem, Ticket

User = get_user_model()

@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.console.EmailBackend",
)
class CheckoutTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="buyer", email="buyer@x.test", password="Pw123456!")
        cls.offer = Offer.objects.create(
            name="Pack Duo",
            offer_type=Offer.DUO if hasattr(Offer, "DUO") else "duo",
            price=Decimal("49.90"),
            description="Deux personnes"
        )
        # Assure un Profile avec signup_key (clé 1)
        Profile.objects.get_or_create(user=cls.user)

    def setUp(self):
        # MEDIA temp pour ne pas salir le repo
        self._tmp_media = tempfile.mkdtemp(prefix="media-tests-")
        self._media_override = override_settings(MEDIA_ROOT=self._tmp_media)
        self._media_override.enable()
        self.client.login(username="buyer", password="Pw123456!")
        # Panier: dict {offer_id: qty} (adapte si tu utilises une liste)
        session = self.client.session
        session["cart"] = {str(self.offer.id): 1}
        session.save()

    def tearDown(self):
        self._media_override.disable()
        shutil.rmtree(self._tmp_media, ignore_errors=True)

    def test_checkout_creates_paid_order_and_ticket_and_clears_cart(self):
        url = reverse("checkout")  # -> à implémenter
        # Simule un "paiement" mock côté vue (POST sans appel externe)
        resp = self.client.post(url, data={"confirm": "1"}, follow=True)
        self.assertEqual(resp.status_code, 200)

        # 1) Order payé + OrderItem créé
        self.assertEqual(Order.objects.count(), 1)
        order = Order.objects.first()
        self.assertEqual(order.user, self.user)
        self.assertEqual(order.status, "paid")          # contrat: status "paid"
        self.assertTrue(order.purchase_key)             # clé 2 générée au checkout
        self.assertEqual(OrderItem.objects.count(), 1)
        item = OrderItem.objects.first()
        self.assertEqual(item.offer_id, self.offer.id)
        self.assertEqual(item.quantity, 1)
        self.assertEqual(item.unit_price, self.offer.price)

        # 2) Ticket généré avec final_key = signup_key + purchase_key (concat)
        self.assertEqual(Ticket.objects.count(), 1)
        ticket = Ticket.objects.first()
        profile = Profile.objects.get(user=self.user)
        self.assertTrue(ticket.final_key.startswith(profile.signup_key))
        self.assertIn(order.purchase_key, ticket.final_key)

        # 3) QR code image enregistrée sous MEDIA_ROOT/qrcodes/
        self.assertTrue(ticket.qrcode_image.name.startswith("qrcodes/"))
        path = os.path.join(settings.MEDIA_ROOT, ticket.qrcode_image.name)
        self.assertTrue(os.path.exists(path))
        self.assertGreater(os.path.getsize(path), 0)

        # 4) Panier vidé
        session = self.client.session
        self.assertFalse(session.get("cart"))

