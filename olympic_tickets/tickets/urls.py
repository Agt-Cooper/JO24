from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView  # on utilise celle-ci

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
    path('logout/', LogoutView.as_view(), name='logout'),

    # CRUD offres
    path('manage/offers/', views.manage_offers_view, name='offers_manage'),

    # (Optionnel) je garde /signup/ si je veux sa propre page
    path('signup/', views.signup_view, name='signup'),
]


# from django.urls import path
# from django.contrib.auth import views as auth_views
# from . import views
#
# urlpatterns = [
#     path('', views.home_view, name='home'),
#     path('bundle/', views.bundle_list_view, name='bundle_list'),
#     path('cart/', views.cart_view, name='cart'),
#     # Màj ou suppression des quantités dans le panier (update / remove)
#     path('cart/update/<int:offer_id>/', views.update_cart_item_view, name='cart_update'),
#     path('cart/remove/<int:offer_id>/', views.remove_from_cart_view, name='cart_remove'),
#     path('add-to-cart/<int:offer_id>/', views.add_to_cart_view, name='add_to_cart'),
#     path('login/', auth_views.LoginView.as_view(template_name='tickets/login.html'), name='login'),
#     path('logout/', auth_views.LogoutView.as_view(), name='logout'),
#     path('signup/', views.signup_view, name='signup'),
#     path('manage/offers/', views.manage_offers_view, name='offers_manage'),
#     path('login/', views.signup_login_view, name='login'),
#     path('logout/', views.LogoutView.as_view(), name='logout'), #si Logout View est utilisé
# ]