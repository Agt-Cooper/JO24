from django.test import TestCase
from tickets.forms import OfferForm, SignupLoginForm

class OfferFormTests(TestCase):
    def test_valid_offer(self):
        form = OfferForm(data={
            "name": "Famille",
            "offer_type": "famille",
            "price": "99.99",
            "description": "4 personnes"
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_price_must_be_positive(self):
        form = OfferForm(data={
            "name": "Solo KO",
            "offer_type": "solo",
            "price": "-10",
            "description": "nope"
        })
        self.assertFalse(form.is_valid())

class SignupLoginFormTests(TestCase):
    def test_invalid_password_confirmation(self):
        form = SignupLoginForm(data={
            "first_name": "A",
            "last_name": "B",
            "email": "a@b.com",
            "password1": "abc123456789",
            "password2": "different"
        })
        self.assertFalse(form.is_valid())
        self.assertIn("password2", form.errors)

    def test_rejects_too_short_password(self):
        """
        Vérifie que les mots de passe trop courts sont rejetés
        (en lien avec validators configurés dans settings).
        """
        form = SignupLoginForm(data={
            "first_name": "Alice",
            "last_name": "Martin",
            "email": "alice@example.com",
            "password1": "short1",
            "password2": "short1",
        })
        self.assertFalse(form.is_valid())
        self.assertIn("password1", form.errors)

    def test_valid_signup_form(self):
        """
        Cas nominal : tout est correct → le formulaire est valide
        et form.save() renvoie un utilisateur.
        """
        form = SignupLoginForm(data={
            "first_name": "Alice",
            "last_name": "Martin",
            "email": "alice@example.com",
            "password1": "MotdepasseUltraFort123!",
            "password2": "MotdepasseUltraFort123!",
        })
        self.assertTrue(form.is_valid(), form.errors)

        user = form.save()
        # Quelques vérifications de cohérence
        self.assertEqual(user.first_name, "Alice")
        self.assertEqual(user.last_name, "Martin")
        self.assertEqual(user.email, "alice@example.com")
        # il doit en résulter un username non vide pour le User
        self.assertTrue(user.username)