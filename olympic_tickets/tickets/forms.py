from django import forms
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
