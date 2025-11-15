from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from tickets.models import Offer, Order, OrderItem

User = get_user_model()

class CheckoutTests(TestCase):
    '''
    checkout panier rempli
    '''
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="u1",
            email="u1@example.com",
            password="pass1234"
        )
        #existence du profil avec signup_key
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

        #Vérification que OrderItem créé avec clé finale + QR
        self.assertEqual(order.items.count(), 1)
        it: OrderItem = order.items.first()
        self.assertEqual(it.offer, self.offer)
        self.assertEqual(it.quantity, 2)
        self.assertTrue(it.final_key())
        self.assertTrue(it.qr_data_uri().startswith("data:image/png;base64,"))

        #Vide le panier
        session = self.client.session
        self.assertEqual(session.get("cart"), {})

class CheckoutEmptyCartTests(TestCase):
    '''
    vérification avec panier vide
    '''
    def setUp(self):
        self.user = User.objects.create_user(
            username="checkout_user",
            email="checkout@example.com",
            password="StrongPassw0rd!"
        )
        self.client.login(username="checkout_user", password="StrongPassw0rd!")

    def test_checkout_get_with_empty_cart_redirects_with_message(self):
        """
        Si le panier est vide (aucune clé 'cart' ou dict vide),
        GET /checkout doit rediriger et afficher un message d'erreur.
        """
        # S'assurer que la session contient un panier vide
        session = self.client.session
        session["cart"] = {}
        session.save()

        url = reverse("checkout")
        # follow=True pour suivre la redirection et récupérer la page finale + messages
        resp = self.client.get(url, follow=True)

        # Vérifie la redirection vers la page des offres
        self.assertRedirects(resp, reverse("bundle_list"))

        # Vérifie que le message "Votre panier est vide." est présent
        messages = list(resp.context["messages"])
        self.assertTrue(
            any("Votre panier est vide" in m.message for m in messages),
            "Le message d'erreur sur le panier vide devrait être affiché."
        )
