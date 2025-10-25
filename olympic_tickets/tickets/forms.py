from decimal import Decimal

from django import forms
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils.text import slugify

from django.contrib.auth import get_user_model, password_validation
from django.contrib.auth.base_user import BaseUserManager  #permet de normaliser l'email

from .models import Offer

User = get_user_model()  # Le mettre ici évite de le remettre partout, on factorise donc l'accès au modèle utilisateur

# Les offres
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
        if price is None:
            raise ValidationError("Le prix est requis.")
        if price < 0:
            raise ValidationError("Le prix ne peut pas être négatif.")
        # Forcer 2 décimales
        return price.quantize(Decimal("0.01"))

# signup avec username = nom_prenom
class SignupLoginForm(forms.Form):
    first_name = forms.CharField(label="Prénom", max_length=30, widget=forms.TextInput(attrs={"autocomplete": "given-name"}))
    last_name  = forms.CharField(label="Nom", max_length=30, widget=forms.TextInput(attrs={"autocomplete": "family-name"}))
    email      = forms.EmailField(label="Email", widget=forms.EmailInput(attrs={"autocomplete": "email"}))
    password1  = forms.CharField(label="Mot de passe", widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}), help_text=password_validation.password_validators_help_text_html(),)
    password2  = forms.CharField(label="Confirmer le mot de passe", widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}))
#Voir si je garde les attrs (au dessus)

#cleaners de champs
    def clean_first_name(self):
        #strip + capitalisation simple
        return (self.cleaned_data.get("first_name") or "").strip().title()

    def clean_last_name(self):
        return (self.cleaned_data.get("last_name") or "").strip().title()

    def clean_email(self):
        raw = (self.cleaned_data.get("email") or "").strip()
        email = BaseUserManager.normalize_email(raw) #normalisation fiable
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("Un compte avec cet email existe déjà.")
        return email
#clean global
    def clean(self):
        cleaned = super().clean()
        p1, p2 = cleaned.get("password1"), cleaned.get("password2")
        if p1 and p2 and p1 != p2:
            self.add_error("password2", "Les mots de passe ne correspondent pas.")

        # Valide la robustesse du mot de passe (avec contexte utilisateur minimal)
        if p1:
            tmp_user = User(
                username="__tmp__",
                email=cleaned.get("email") or "",
                first_name=cleaned.get("first_name") or "",
                last_name=cleaned.get("last_name") or "",
            )
            try:
                password_validation.validate_password(p1, user=tmp_user)
            except ValidationError as e:
                self.add_error("password1", e)
        return cleaned

#generation du username (possible changement)
    def _make_unique_username(self, first_name: str, last_name: str) -> str:
        """
        Concaténation du nom et prénom en slug : nom_prenom
        Garantit l'unicité (avec modèle nom_prenom1 etc
        """
        base = slugify(f"{last_name}_{first_name}") or "user" #faire avec _ ou alors un espace entre les deux ????
        max_len = 150
        base = base[:max_len]
        username = base
        c = 1
        while User.objects.filter(username=username).exists():
            suf = str(c)
            username = f"{base[:max_len - len(suf)]}{suf}"
            c += 1
        return username

#Creation de l'utilisateur
    @transaction.atomic
    def save(self):
        data = self.cleaned_data
        first_name = data["first_name"]
        last_name = data["last_name"]
        email = data["email"] #déjà normalisé
        username = self._make_unique_username(first_name, last_name)

        user = User.objects.create_user(
            username=username,
            email=email,  # déjà normalisé en clean_email
            password=data["password1"],
            first_name=first_name,
            last_name=last_name,
        )
        return user