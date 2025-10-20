from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.models.deletion import ProtectedError
from django.utils import timezone

from tickets.models import Offer, Order, OrderItem, Profile  # Profile utilisé ailleurs dans ton projet

User = get_user_model()


class OfferModelTests(TestCase):
    def test_str_uses_display_label(self):
        o = Offer.objects.create(
            name="Pack Duo",
            offer_type=Offer.DUO,   # 'duo'
            price=Decimal("49.90"),
            description="Deux personnes",
        )
        self.assertEqual(str(o), "Pack Duo - Duo (2 personnes)")

    def test_offer_type_must_be_in_choices_via_full_clean(self):
        o = Offer(
            name="Pack X",
            offer_type="xxx",  # invalide
            price=Decimal("10.00"),
        )
        with self.assertRaises(ValidationError):
            o.full_clean()  # choices sont vérifiés ici (pas au simple save())

    def test_price_respects_max_digits_decimal_places(self):
        # max_digits=6, decimal_places=2 -> max 9999.99
        valid = Offer(
            name="Max OK",
            offer_type=Offer.SOLO,
            price=Decimal("9999.99"),
        )
        valid.full_clean()  # ne doit pas lever

        too_big = Offer(
            name="Trop grand",
            offer_type=Offer.SOLO,
            price=Decimal("10000.00"),
        )
        with self.assertRaises(ValidationError):
            too_big.full_clean()


class OrderModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="alice", password="Pw123456!")

    def test_defaults_and_str(self):
        order = Order.objects.create(user=self.user)  # status par défaut 'pending'
        self.assertEqual(order.status, "pending")
        # created_at doit être renseigné (proche de maintenant)
        self.assertIsNotNone(order.created_at)
        self.assertTrue(abs((timezone.now() - order.created_at).total_seconds()) < 5)
        # __str__
        s = str(order)
        self.assertIn("Order #", s)
        self.assertIn(self.user.username, s)
        self.assertIn("pending", s)


class OrderItemModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="bob", password="Pw123456!")
        self.order = Order.objects.create(user=self.user, status="pending")
        self.offer = Offer.objects.create(
            name="Solo",
            offer_type=Offer.SOLO,
            price=Decimal("19.90"),
            description="1 personne",
        )

    def test_relations_and_reverse_manager(self):
        item = OrderItem.objects.create(
            order=self.order,
            offer=self.offer,
            quantity=2,
            unit_price=self.offer.price,
        )
        # Reverse 'items' sur Order
        self.assertEqual(self.order.items.count(), 1)
        self.assertEqual(self.order.items.first(), item)

    def test_cascade_delete_on_order(self):
        OrderItem.objects.create(
            order=self.order,
            offer=self.offer,
            quantity=1,
            unit_price=self.offer.price,
        )
        self.assertEqual(OrderItem.objects.count(), 1)
        # Supprimer l'Order supprime ses items (on_delete=CASCADE)
        self.order.delete()
        self.assertEqual(OrderItem.objects.count(), 0)

    def test_protect_delete_on_offer(self):
        OrderItem.objects.create(
            order=self.order,
            offer=self.offer,
            quantity=1,
            unit_price=self.offer.price,
        )
        with self.assertRaises(ProtectedError):
            self.offer.delete()

    def test_quantity_negative_rejected_by_full_clean(self):
        # PositiveIntegerField rejette < 0 via validation (full_clean)
        bad = OrderItem(
            order=self.order,
            offer=self.offer,
            quantity=-1,
            unit_price=self.offer.price,
        )
        with self.assertRaises(ValidationError):
            bad.full_clean()

    def test_unit_price_respects_decimal_constraints(self):
        # max_digits=8, decimal_places=2 -> max 999999.99
        ok = OrderItem(
            order=self.order,
            offer=self.offer,
            quantity=1,
            unit_price=Decimal("999999.99"),
        )
        ok.full_clean()  # doit passer

        too_big = OrderItem(
            order=self.order,
            offer=self.offer,
            quantity=1,
            unit_price=Decimal("1000000.00"),
        )
        with self.assertRaises(ValidationError):
            too_big.full_clean()
