from django.test import TestCase
from tickets.forms import OfferForm

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