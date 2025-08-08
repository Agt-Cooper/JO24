from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('offres/', views.bundle_list_view, name='bundle_list'),
    path('panier/', views.cart_view, name='cart'),
    path('ajouter/<int:offer_id>/', views.add_to_cart_view, name='add_to_cart'),
]