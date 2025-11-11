from django.test import TestCase, RequestFactory
from tickets.context_processors import cart_count


class CartCountContextProcessorTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_cart_count_with_dict(self):
        """
        Panier au format moderne: {'1': 2, '3': 1} => 3 articles au total.
        """
        request = self.factory.get("/")
        request.session = {"cart": {"1": 2, "3": 1}}

        ctx = cart_count(request)
        self.assertEqual(ctx["cart_count"], 3)

    def test_cart_count_with_list(self):
        """
        Ancien format: [1, 1, 2] => len = 3
        """
        request = self.factory.get("/")
        request.session = {"cart": [1, 1, 2]}

        ctx = cart_count(request)
        self.assertEqual(ctx["cart_count"], 3)
