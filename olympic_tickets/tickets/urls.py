from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('bundle/', views.bundle_list_view, name='bundle_list'),
    path('cart/', views.cart_view, name='cart'),
    path('add-to-cart/<int:offer_id>/', views.add_to_cart_view, name='add_to_cart'),
    path('login/', auth_views.LoginView.as_view(template_name='tickets/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('signup/', views.signup_view, name='signup'),
    path('manage/offers/', views.manage_offers_view, name='offers_manage'),
]