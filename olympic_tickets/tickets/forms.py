from django import forms
from django.contrib.auth.models import User

class SignupLoginForm(forms.Form):
    first_name = forms.CharField(label="Prénom", max_length=30)
    last_name = forms.CharField(label="Nom", max_length=30)
    email = forms.EmailField(label="Email")
    password1 = forms.CharField(label="Mot de passe", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirmer le mot de passe", widget=forms.PasswordInput)

    def clean_email(self):
        email = self.cleaned_data["email"].strip()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Un compte avec cet email existe déjà.")
        return email

    def clean(self):
        cleaned = super().clean()
        p1, p2 = cleaned.get("password1"), cleaned.get("password2")
        if p1 and p2 and p1 != p2:
            self.add_error("password2", "Les mots de passe ne correspondent pas.")
        return cleaned

    def _make_unique_username(self, first_name: str, last_name: str) -> str:
        base = f"{first_name}.{last_name}".lower()
        # slugification simple
        import re
        base = re.sub(r"[^a-z0-9\.]+", "", base.replace(" ", "").replace("'", ""))
        if not base:
            base = "user"
        username = base
        c = 1
        from django.contrib.auth.models import User
        while User.objects.filter(username=username).exists():
            c += 1
            username = f"{base}{c}"
        return username

    def save(self):
        data = self.cleaned_data
        username = self._make_unique_username(data["first_name"], data["last_name"])
        user = User.objects.create_user(
            username=username,
            email=data["email"].strip(),
            password=data["password1"],
            first_name=data["first_name"].strip(),
            last_name=data["last_name"].strip(),
        )
        return user


# from django import forms
# from .models import Offer
#
# class OfferForm(forms.ModelForm):
#     class Meta:
#         model = Offer
#         fields = ["name", "offer_type", "description", "price"]
#         labels = {
#             "name": "Nom de l’offre",
#             "offer_type": "Type d’offre",
#             "description": "Description",
#             "price": "Prix (€)",
#         }
