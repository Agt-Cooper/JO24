from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from decimal import Decimal
import tempfile, shutil, os

from tickets.models import Offer, Profile, Order, OrderItem, Ticket

User = get_user_model()

@override_settings(EMAIL_BACKEND="django.core.mail.backends.console.EmailBackend")
class TicketQRTests(TestCase):
    def setUp(self):
        self._tmp_media = tempfile.mkdtemp(prefix="media-tests-")
        self._media_override = override_settings(MEDIA_ROOT=self._tmp_media)
        self._media_override.enable()

        self.user = User.objects.create_user(username="qruser", email="qr@x.test", password="Pw123456!")
        Profile.objects.get_or_create(user=self.user)
        self.offer = Offer.objects.create(name="Solo", offer_type="solo", price=Decimal("19.90"), description="1p")

        self.client.login(username="qruser", password="Pw123456!")
        s = self.client.session
        s["cart"] = {str(self.offer.id): 1}
        s.save()

        # Checkout pour créer le ticket + QR
        self.client.post(reverse("checkout"), data={"confirm": "1"}, follow=True)
        self.ticket = Ticket.objects.first()

    def tearDown(self):
        self._media_override.disable()
        shutil.rmtree(self._tmp_media, ignore_errors=True)

    def test_qr_image_file_exists_and_is_under_qrcodes(self):
        self.assertIsNotNone(self.ticket)
        self.assertTrue(self.ticket.qrcode_image.name.startswith("qrcodes/"))
        path = os.path.join(self._tmp_media, self.ticket.qrcode_image.name)
        self.assertTrue(os.path.exists(path))
        self.assertGreater(os.path.getsize(path), 0)
