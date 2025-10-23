from django.core.management.base import BaseCommand, CommandError
from decimal import Decimal
from django.db.models import Q
from tickets.models import Offer

class Command(BaseCommand):
    help = (
        "Crée (ou met à jour) des offres Solo/Duo/Famille pour chaque épreuve donnée, "
        "avec PRIX FIXES codés en dur.\n"
        "Usage :\n"
        "  python manage.py seed_offers --events 'Natation,Athlétisme,Gymnastique'\n"
        "Options :\n"
        "  --reset  -> supprime d'abord les offres existantes pour ces épreuves\n"
    )

    # === PRIX FIXES COMMUNS À TOUTES LES ÉPREUVES ===
    PRICE_SOLO = Decimal("25.00")
    PRICE_DUO = Decimal("40.00")
    PRICE_FAMILLE = Decimal("75.00")

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
            help="Supprime les offres existantes des épreuves ciblées avant de (re)créer.",
        )

    def handle(self, *args, **opts):
        # 1) Parse des épreuves
        raw = opts["events"]
        events = [e.strip() for e in raw.split(",") if e.strip()]
        if not events:
            raise CommandError("Aucune épreuve fournie. Utilise --events 'Natation,Athlétisme, Gymnastique'.")

        # 2) Reset optionnel (supprime les deux styles : ancien 'Épreuve - Solo' et nouveau 'name=Épreuve')
        if opts["reset"]:
            q = Q()
            for e in events:
                q |= Q(name=e) | Q(name__startswith=f"{e} - ")
            deleted, _ = Offer.objects.filter(q).delete()
            self.stdout.write(self.style.WARNING(f"Reset : {deleted} offre(s) supprimée(s)."))

        # 3) Matrice (type, prix, description)
        matrix = [
            ("solo",    self.PRICE_SOLO,    "1 personne"),
            ("duo",     self.PRICE_DUO,     "2 personnes"),
            ("famille", self.PRICE_FAMILLE, "4 personnes"),
        ]

        # 4) Upsert (name = épreuve, clé = (name, offer_type))
        created, updated = 0, 0
        for epreuve in events:
            for offer_type, price, ppl in matrix:
                defaults = dict(
                    name=epreuve,
                    offer_type=offer_type,
                    description=f"Accès {epreuve} - {ppl}",
                    price=price,
                )
                obj, was_created = Offer.objects.update_or_create(
                    name=epreuve,
                    offer_type=offer_type,
                    defaults=defaults,
                )
                if was_created:
                    created += 1
                    self.stdout.write(self.style.SUCCESS(f"Créé : {obj.name} ({offer_type})"))
                else:
                    updated += 1
                    self.stdout.write(self.style.NOTICE(f"MàJ  : {obj.name} ({offer_type})"))

        self.stdout.write(self.style.SUCCESS(
            f"Terminé. Créés: {created} | Mis à jour: {updated} | Épreuves: {len(events)}"
        ))
