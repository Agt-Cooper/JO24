from decimal import Decimal
from django import forms
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from django.contrib.auth import get_user_model, password_validation

from .models import Offer

User = get_user_model()  # Le mettre ici évite de le remettre partout, on factorise donc l'accès au modèle utilisateur


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


class SignupLoginForm(forms.Form):
    first_name = forms.CharField(label="Prénom", max_length=30, widget=forms.TextInput(attrs={"autocomplete": "given-name"}))
    last_name  = forms.CharField(label="Nom", max_length=30, widget=forms.TextInput(attrs={"autocomplete": "family-name"}))
    email      = forms.EmailField(label="Email", widget=forms.EmailInput(attrs={"autocomplete": "email"}))
    password1  = forms.CharField(label="Mot de passe", widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}))
    password2  = forms.CharField(label="Confirmer le mot de passe", widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}))
#Voir si je garde les attrs (au dessus)
    def clean_email(self):
        raw = (self.cleaned_data.get("email") or "").strip()
        email = raw.lower()  # normalisation simple avant email = BaseUserManager.normalize_email(raw) attention, retiré de from
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("Un compte avec cet email existe déjà.")
        return email

    def clean(self):
        cleaned = super().clean()
        p1, p2 = cleaned.get("password1"), cleaned.get("password2")
        if p1 and p2 and p1 != p2:
            self.add_error("password2", "Les mots de passe ne correspondent pas.")

        # Valide la robustesse du mot de passe (avec contexte utilisateur)
        if p1:
            tmp_user = User(username="tmp",
                            email=cleaned.get("email") or "",
                            first_name=cleaned.get("first_name") or "",
                            last_name=cleaned.get("last_name") or "")
            try:
                password_validation.validate_password(p1, user=tmp_user)
            except ValidationError as e:
                self.add_error("password1", e)
        return cleaned

    def _make_unique_username(self, first_name: str, last_name: str) -> str:
        base = slugify(f"{first_name}.{last_name}") or "user"
        max_len = 150
        base = base[:max_len]
        username = base
        c = 1
        while User.objects.filter(username=username).exists():
            suf = str(c)
            username = base[: max_len - len(suf)] + suf
            c += 1
        return username

    @transaction.atomic
    def save(self):
        data = self.cleaned_data
        username = self._make_unique_username(data["first_name"].strip(), data["last_name"].strip())
        user = User.objects.create_user(
            username=username,
            email=data["email"],  # déjà normalisé en clean_email
            password=data["password1"],
            first_name=data["first_name"].strip(),
            last_name=data["last_name"].strip(),
        )
        return user