from django.core.management.base import BaseCommand, CommandError
from decimal import Decimal
from tickets.models import Offer

class Command(BaseCommand):
    help = (
        "Crée des offres Solo/Duo/Famille pour chaque épreuve indiquée.\n"
        "Usage :\n"
        "  python manage.py seed_offers --events 'Natation,Athlétisme,Gymnastique'\n"
        "Options :\n"
        "  --reset         -> supprime d'abord les offres liées aux épreuves ciblées\n"
        "  --solo 25.00    -> prix solo personnalisé (par défaut 25.00)\n"
        "  --duo  40.00    -> prix duo  personnalisé (par défaut 40.00)\n"
        "  --famille 75.00-> prix famille personnalisé (par défaut 75.00)\n"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--events",
            type=str,
            required=True,
            help="Liste d’épreuves séparées par des virgules (ex: 'Natation,Athlétisme,Gymnastique').",
        )
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Supprime les offres existantes des épreuves ciblées avant de créer.",
        )
        parser.add_argument("--solo", type=str, default="25.00", help="Prix Solo (default 25.00)")
        parser.add_argument("--duo", type=str, default="40.00", help="Prix Duo (default 40.00)")
        parser.add_argument("--famille", type=str, default="75.00", help="Prix Famille (default 75.00)")

    def handle(self, *args, **opts):
        # 1) Parse des épreuves
        raw = opts["events"]
        events = [e.strip() for e in raw.split(",") if e.strip()]
        if not events:
            raise CommandError("Aucune épreuve fournie. Utilise --events 'Natation,Athlétisme'.")

        # 2) Prix
        try:
            price_solo = Decimal(opts["solo"])
            price_duo = Decimal(opts["duo"])
            price_famille = Decimal(opts["famille"])
        except Exception as exc:
            raise CommandError(f"Prix invalide : {exc}")

        # 3) Suppression (optionnelle) des offres existantes ciblées
        #    On supprime en filtrant par les noms générés "{epreuve} - Solo/Duo/Famille"
        if opts["reset"]:
            to_delete = []
            for e in events:
                to_delete.extend([
                    f"{e} - Solo",
                    f"{e} - Duo",
                    f"{e} - Famille",
                ])
            deleted_count, _ = Offer.objects.filter(name__in=to_delete).delete()
            self.stdout.write(self.style.WARNING(f"Reset : {deleted_count} offre(s) supprimée(s)."))

        # 4) Génération / upsert des offres
        created, updated = 0, 0
        for epreuve in events:
            rows = [
                {
                    "name": f"{epreuve}",
                    "offer_type": "solo",
                    "description": f"Accès {epreuve} - 1 personne",
                    "price": price_solo,
                },
                {
                    "name": f"{epreuve}",
                    "offer_type": "duo",
                    "description": f"Accès {epreuve} - 2 personnes",
                    "price": price_duo,
                },
                {
                    "name": f"{epreuve}",
                    "offer_type": "famille",
                    "description": f"Accès {epreuve} - 4 personnes",
                    "price": price_famille,
                },
            ]
            for data in rows:
                obj, was_created = Offer.objects.update_or_create(
                    name=data["name"],  # clé fonctionnelle : le nom complet sert d’identifiant
                    defaults=data,
                )
                if was_created:
                    created += 1
                    self.stdout.write(self.style.SUCCESS(f"Créé : {obj.name}"))
                else:
                    updated += 1
                    self.stdout.write(self.style.NOTICE(f"MàJ  : {obj.name}"))

        self.stdout.write(self.style.SUCCESS(
            f"Terminé. Créés: {created} | Mis à jour: {updated} | Épreuves: {len(events)}"
        ))
