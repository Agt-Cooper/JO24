from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Offer

@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ("name", "offer_type", "price")
    list_filter = ("offer_type",)
    search_fields = ("name", "description")
