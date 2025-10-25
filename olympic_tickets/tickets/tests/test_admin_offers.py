from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()

class OffersManageTests(TestCase):
    def setUp(self):
        self.url = reverse("offers_manage")
        self.staff = User.objects.create_user(username="admin", password="Pw123456!") #le staff
        self.user = User.objects.create_user(username="user", password="Pw123456!") #le pas staff
        self.staff.is_staff = True
        self.staff.save()

    def test_non_staff_is_redirected_to_admin_login(self):
        self.client.login(username="user", password="Pw123456!")
        resp = self.client.get(self.url, follow=False)
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/admin/login", resp["Location"])
        self.assertIn("next=", resp["Location"])  # redirection

    def test_anonymous_is_redirected_to_admin_login(self):
        resp = self.client.get(self.url, follow=False)
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/admin/login", resp["Location"])

    def test_staff_can_access(self):
        self.client.login(username="admin", password="Pw123456!")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Gérer les offres")