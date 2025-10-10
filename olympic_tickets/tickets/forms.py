from decimal import Decimal

from django import forms
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from django.contrib.auth import get_user_model, password_validation
from django.contrib.auth.base_user import BaseUserManager

from .models import Offer


class OfferForm(forms.ModelForm):
    class Meta:
        model = Offer
        fields = ["name", "offer_type", "description", "price"]
        labels = {
            "name": "Nom de l’offre",
            "offer_type": "Type d’offre",
            "description": "Description",
            "price": "Prix (€)",
        }
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
        }

    def clean_price(self):
        price = self.cleaned_data["price"]
        # Suppose que Offer.price est un DecimalField
        if price is None:
            raise ValidationError("Le prix est requis.")
        if price < 0:
            raise ValidationError("Le prix ne peut pas être négatif.")
        # Optionnel : forcer 2 décimales
        return price.quantize(Decimal("0.01"))


class SignupLoginForm(forms.Form):
    first_name = forms.CharField(label="Prénom", max_length=30)
    last_name = forms.CharField(label="Nom", max_length=30)
    email = forms.EmailField(label="Email")
    password1 = forms.CharField(label="Mot de passe", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirmer le mot de passe", widget=forms.PasswordInput)

    def clean_email(self):
        UserModel = get_user_model()
        raw = self.cleaned_data["email"].strip()
        email = BaseUserManager.normalize_email(raw)
        # Vérifie la dispo (insensible à la casse)
        if UserModel.objects.filter(email__iexact=email).exists():
            raise ValidationError("Un compte avec cet email existe déjà.")
        return email

    def clean(self):
        cleaned = super().clean()
        p1, p2 = cleaned.get("password1"), cleaned.get("password2")
        if p1 and p2 and p1 != p2:
            self.add_error("password2", "Les mots de passe ne correspondent pas.")
        # Valide la robustesse du mot de passe avec les validateurs Django
        # (on passe un user “virtuel” pour donner du contexte aux validateurs)
        email = cleaned.get("email")
        fn = cleaned.get("first_name") or ""
        ln = cleaned.get("last_name") or ""
        if p1:
            try:
                UserModel = get_user_model()
                tmp_user = UserModel(username="tmp", email=email, first_name=fn, last_name=ln)
                password_validation.validate_password(p1, user=tmp_user)
            except ValidationError as e:
                self.add_error("password1", e)
        return cleaned

    def _make_unique_username(self, first_name: str, last_name: str) -> str:
        """
        username unique, slugifié, tronqué à 150 chars (limite Django).
        """
        UserModel = get_user_model()
        base = slugify(f"{first_name}.{last_name}") or "user"
        # Garde un peu de marge pour le suffixe numérique
        max_len = 150
        base = base[:max_len]
        username = base
        c = 1
        while UserModel.objects.filter(username=username).exists():
            suffix = str(c)
            username = (base[: max_len - len(suffix)] + suffix)
            c += 1
        return username

    @transaction.atomic
    def save(self):
        UserModel = get_user_model()
        data = self.cleaned_data

        username = self._make_unique_username(
            data["first_name"].strip(),
            data["last_name"].strip(),
        )
        email = BaseUserManager.normalize_email(data["email"])
        # Création via manager (gère hash + user_is_active etc.)
        user = UserModel.objects.create_user(
            username=username,
            email=email,
            password=data["password1"],
            first_name=data["first_name"].strip(),
            last_name=data["last_name"].strip(),
        )
        return user


# from django import forms
# from django.contrib.auth.models import User
# from .models import Offer
#
# class OfferForm(forms.ModelForm):
#     class Meta:
#         model = Offer
#         fields = ["name", "offer_type", "description", "price"]
#         labels = {
#             "name": "Nom de l’offre",
#             "offer_type": "Type d’offre",
#             "description: "Description",
#             "price": "Prix (€)",
#         }
#
# class SignupLoginForm(forms.Form):
#     first_name = forms.CharField(label="Prénom", max_length=30)
#     last_name = forms.CharField(label="Nom", max_length=30)
#     email = forms.EmailField(label="Email")
#     password1 = forms.CharField(label="Mot de passe", widget=forms.PasswordInput)
#     password2 = forms.CharField(label="Confirmer le mot de passe", widget=forms.PasswordInput)
#
#     def clean_email(self):
#         email = self.cleaned_data["email"].strip()
#         if User.objects.filter(email__iexact=email).exists():
#             raise forms.ValidationError("Un compte avec cet email existe déjà.")
#         return email
#
#     def clean(self):
#         cleaned = super().clean()
#         p1, p2 = cleaned.get("password1"), cleaned.get("password2")
#         if p1 and p2 and p1 != p2:
#             self.add_error("password2", "Les mots de passe ne correspondent pas.")
#         return cleaned
#
#     def _make_unique_username(self, first_name: str, last_name: str) -> str:
#         base = f"{first_name}.{last_name}".lower()
#         # slugification simple
#         import re
#         base = re.sub(r"[^a-z0-9\.]+", "", base.replace(" ", "").replace("'", ""))
#         if not base:
#             base = "user"
#         username = base
#         c = 1
#         from django.contrib.auth.models import User
#         while User.objects.filter(username=username).exists():
#             c += 1
#             username = f"{base}{c}"
#         return username
#
#     def save(self):
#         data = self.cleaned_data
#         username = self._make_unique_username(data["first_name"], data["last_name"])
#         user = User.objects.create_user(
#             username=username,
#             email=data["email"].strip(),
#             password=data["password1"],
#             first_name=data["first_name"].strip(),
#             last_name=data["last_name"].strip(),
#         )
#         return user