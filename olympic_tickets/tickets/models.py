# Create your models here.
from django.db import models

class Offer(models.Model):
    SOLO = 'solo'
    DUO = 'duo'
    FAMILLE = 'famille'

    OFFER_TYPES = [
        (SOLO, 'Solo (1 personne)'),
        (DUO, 'Duo (2 personnes)'),
        (FAMILLE, 'Famille (4 personnes)'),
    ]

    name = models.CharField(max_length=100)
    offer_type = models.CharField(max_length=10, choices=OFFER_TYPES)
    description = models.TextField()
    price = models.DecimalField(max_digits=6, decimal_places=2)

    def __str__(self):
        return self.name