from django.test import TestCase
from django.contrib.auth import get_user_model
from tickets.forms import OfferForm, SignupLoginForm
from tickets.models import Profile

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
        #self.assertFalse(form.is_valid())
        #self.assertIn("password2", form.errors)

    def test_rejects_too_short_password(self):
        """
        Ca vérifie que les mots de passe trop courts sont rejetés
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
        Il faut que tout soit correcte : le formulaire est valide
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
        # il faut un username non vide pour le User
        self.assertTrue(user.username)

    def test_valid_signup_creates_user_and_profile_with_signup_key(self):
        """
        Le formulaire valide doit créer un user + son profil avec signup_key non vide.
        """
        form = SignupLoginForm(data={
            "first_name": "Jean",
            "last_name": "Dupont",
            "email": "jean.dupont@example.com",
            "password1": "MotDePasseHyperSecurise1",
            "password2": "MotDePasseHyperSecurise1",
        })
        self.assertTrue(form.is_valid(), form.errors)

        user = form.save()
        User = get_user_model()
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(user.email, "jean.dupont@example.com")

        # Profil auto-créé + signup_key non vide
        profile = Profile.objects.get(user=user)
        self.assertTrue(profile.signup_key)
        self.assertGreater(len(profile.signup_key), 10)

    def test_rejects_duplicate_email(self):
        """
        Si l'email existe déjà, le formulaire doit être invalide (clean_email).
        """
        User = get_user_model()
        User.objects.create_user(
            username="existing",
            email="dup@example.com",
            password="SomePassword1234"
        )

        form = SignupLoginForm(data={
            "first_name": "Paul",
            "last_name": "Martin",
            "email": "dup@example.com",
            "password1": "AutreMotDePasse1234",
            "password2": "AutreMotDePasse1234",
        })

        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)