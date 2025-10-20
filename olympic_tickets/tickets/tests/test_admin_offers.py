from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()

class OffersManageTests(TestCase):
    def setUp(self):
        self.url = reverse("offers_manage")
        self.staff = User.objects.create_user(username="admin", password="Pw123456!")
        self.staff.is_staff = True
        self.staff.save()
        self.user = User.objects.create_user(username="user", password="Pw123456!")

    def test_non_staff_cannot_access(self):
        self.client.login(username="user", password="Pw123456!")
        resp = self.client.get(self.url)
        self.assertNotEqual(resp.status_code, 200)  # 302 (login) ou 403 selon décorateur

    def test_staff_can_access(self):
        self.client.login(username="admin", password="Pw123456!")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Gestion des offres")