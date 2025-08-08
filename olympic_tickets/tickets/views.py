# Create your views here.
from django.shortcuts import render, get_object_or_404, redirect
from .models import Offer

# Accueil
def home_view(request):
    return render(request, 'tickets/home.html')

# Liste des offres
def bundle_list_view(request):
    offers = Offer.objects.all()
    return render(request, 'tickets/bundle.html', {'offers': offers})

# Panier simulé (données en session pour simplifier)
def cart_view(request):
    cart = request.session.get('cart', [])
    items = []
    total = 0

    for offer_id in cart:
        offer = get_object_or_404(Offer, id=offer_id)
        items.append({'offer': offer})
        total += offer.price

    return render(request, 'tickets/cart.html', {'cart': items, 'total_price': total})

# Ajouter au panier
def add_to_cart_view(request, offer_id):
    cart = request.session.get('cart', [])
    cart.append(offer_id)
    request.session['cart'] = cart
    return redirect('cart')