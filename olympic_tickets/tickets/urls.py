from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('', views.home_view, name='home'),
    path('bundle/', views.bundle_list_view, name='bundle_list'),
    path('cart/', views.cart_view, name='cart'),

    # Panier (AJAX)
    path('cart/update/<int:offer_id>/', views.update_cart_item_view, name='cart_update'),
    path('cart/remove/<int:offer_id>/', views.remove_from_cart_view, name='cart_remove'),
    path('add-to-cart/<int:offer_id>/', views.add_to_cart_view, name='add_to_cart'),

    # Auth perso (inscription sur la page "login")
    path('login/', views.signup_login_view, name='login'),
    path('signup/', views.signup_login_view, name='signup'),# (Optionnel) je garde /signup/ si je veux sa propre page#-->path('signup/', views.signup_view, name='signup'), # optionnel si sur même page
    path('signin/', views.signin_view, name='signin'), # Ajout pour la partie pop up déjà un compte
    path('logout/', LogoutView.as_view(next_page='home'), name='logout'),

    #lié au staff_member_required pour la redirection
    path('offers/manage/', views.offers_manage_view, name='offers_manage'),

    #en rapport avec la deuxième clé, paiement
    path('checkout/', views.checkout_view, name='checkout'),
    path('mes-achats/', views.my_purchases, name='my_purchases'),
]