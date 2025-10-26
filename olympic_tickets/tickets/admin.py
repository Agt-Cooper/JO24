from django.contrib import admin
from django.db.models import Sum, Q
from django.db.models.functions import Coalesce

from .models import Offer


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ("name", "offer_type", "price", "sold_qty")
    list_filter = ("offer_type",)
    search_fields = ("name", "description")

    def get_queryset(self, request):
        """
        Annote chaque Offer avec :
        - _sold_qty : somme des quantités vendues (OrderItem.quantity)
        On ne compte que les Orders dont status = 'paid'.
        """
        qs = super().get_queryset(request)
        return qs.annotate(
            _sold_qty=Coalesce(
                Sum(
                    "orderitem__quantity",
                    filter=Q(orderitem__order__status="paid"),
                ),
                0,
            )
        )

    def sold_qty(self, obj):
        return obj._sold_qty
    sold_qty.short_description = "Ventes (Qté)"
    sold_qty.admin_order_field = "_sold_qty"


# # Register your models here.
# from django.contrib import admin
# from .models import Offer
#
# @admin.register(Offer)
# class OfferAdmin(admin.ModelAdmin):
#     list_display = ("name", "offer_type", "price")
#     list_filter = ("offer_type",)
#     search_fields = ("name", "description")
