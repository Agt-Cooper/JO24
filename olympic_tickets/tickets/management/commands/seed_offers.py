from django.core.management.base import BaseCommand
from tickets.models import Offer

class Command(BaseCommand):
    help = "Crée des offres par défaut (solo, duo, famille)"

    def handle(self, *args, **kwargs):
        DATA = [
            dict(name="Pack Solo", offer_type="solo", description="1 personne", price="49.00"),
            dict(name="Pack Duo", offer_type="duo", description="2 personnes", price="89.00"),
            dict(name="Pack Famille", offer_type="famille", description="4 personnes", price="149.00"),
        ]

        for item in DATA:
            obj, created = Offer.objects.update_or_create(
                name=item["name"],
                defaults=item,
            )
            action = "Créé" if created else "Déjà existant → mis à jour"
            self.stdout.write(self.style.SUCCESS(f"{action} : {obj.name}"))

        self.stdout.write(self.style.SUCCESS("Seed des offres terminé"))
