# Create your views here.
from django.shortcuts import render, get_object_or_404, redirect
from .models import Offer

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import reverse
from .forms import OfferForm

from django.http import JsonResponse
from django.views.decorators.http import require_POST

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

    #Supporte dict {id/ qty} et ancien format liste
    if isinstance(cart, dict):
        for offer_id, qty in cart.items():
            offer = get_object_or_404(Offer, id=int(offer_id))
            line_total = offer.price * qty
            items.append({'offer': offer, 'quantity': qty, 'line_total': line_total})
            total += offer.price

    else:
        # ancien format: chaque id compte pour 1
        for offer_id in cart:
            offer = get_object_or_404(Offer, id=offer_id)
            line_total = offer.price
            items.append({offer: offer, 'quantity': 1, 'line_total': line_total})
            total += line_total

    return render(request, 'tickets/cart.html', {'cart': items, 'total_price': total})

# Ajouter au panier
@require_POST
def add_to_cart_view(request, offer_id):
    # Récupère la quantité depuis le POST (>=1)
    try:
        qty = int(request.POST.get("quantity", "1"))
    except ValueError:
        qty = 1
    qty = max(1, qty)

    cart = request.session.get('cart', [])

    # Si ton ancien panier est une LISTE d'IDs → on la convertit en DICT {id: qty}
    if isinstance(cart, list):
        new_cart = {}
        for oid in cart:
            k= str(oid)
            new_cart[k] = new_cart.get(k, 0) + 1
        cart = new_cart

    # Maintenant `cart` est un dict { "offer_id": qty }
    key = str(offer_id)
    cart[key] = cart.get(key, 0) + qty  # doit ajouter la quantité choisie

    request.session['cart'] = cart
    request.session.modified = True

    # Requête AJAX → renvoie le compteur total (somme des quantités)
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        total_items = sum(cart.values()) # PLUS UTILE ?? if isinstance(cart, dict) else len(cart)
        return JsonResponse({"ok": True, "cart_count": total_items, "added_qty": qty})

    # Fallback non-AJAX : revenir à la page précédente
    return redirect(request.META.get("HTTP_REFERER") or '/')


# AUTHENTIFICATION

def signup_view(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # connecte l'utilisateur après inscription
            return redirect("home")
    else:
        form = UserCreationForm()
    return render(request, "tickets/signup.html", {"form": form})

# GESTION DES OFFRES (CRUD)

def _is_staff_or_superuser(user):
    """Test utilisé pour restreindre l’accès au CRUD."""
    return user.is_authenticated and (user.is_staff or user.is_superuser)


@login_required
@user_passes_test(_is_staff_or_superuser)
def manage_offers_view(request):
    """
    Page unique de gestion des offres :
    - GET : liste + formulaire (création ou édition si ?edit=<pk>)
    - POST : create / update / delete selon `action`
    """
    from .forms import OfferForm  # import ici pour éviter les boucles

    edit_id = request.GET.get("edit")
    offer_to_edit = None
    if edit_id:
        offer_to_edit = get_object_or_404(Offer, pk=edit_id)

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "create":
            form = OfferForm(request.POST)
            if form.is_valid():
                form.save()
                return redirect(reverse("offers_manage"))

        elif action == "update":
            offer_id = request.POST.get("offer_id")
            offer = get_object_or_404(Offer, pk=offer_id)
            form = OfferForm(request.POST, instance=offer)
            if form.is_valid():
                form.save()
                return redirect(reverse("offers_manage"))

        elif action == "delete":
            offer_id = request.POST.get("offer_id")
            offer = get_object_or_404(Offer, pk=offer_id)
            offer.delete()
            return redirect(reverse("offers_manage"))

        # Si l’action est inconnue → redirection simple
        return redirect(reverse("offers_manage"))

    # GET : afficher formulaire (vide ou édition)
    form = OfferForm(instance=offer_to_edit) if offer_to_edit else OfferForm()
    offers = Offer.objects.order_by("name")

    return render(request, "tickets/offers_manage.html", {
        "offers": offers,
        "form": form,
        "is_editing": bool(offer_to_edit),
        "offer_being_edited": offer_to_edit,
    })

# Les deux vues suivantes concernent l'ajout suppression des quantités dans le panier

def _get_cart_dict(request):
    """Garantit que le panier est un dict {str(offer_id): qty}."""
    cart = request.session.get('cart', {})
    if isinstance(cart, list):
        # rétro-compatibilité
        d = {}
        for oid in cart:
            d[str(oid)] = d.get(str(oid), 0) + 1
        cart = d
    return cart

def _cart_totals(cart):
    """Calcule le total du panier et le nombre total d’articles."""
    total_items = sum(cart.values()) if isinstance(cart, dict) else len(cart)
    total_price = 0
    if isinstance(cart, dict):
        for oid, qty in cart.items():
            offer = get_object_or_404(Offer, id=int(oid))
            total_price += offer.price * qty
    else:
        for oid in cart:
            offer = get_object_or_404(Offer, id=oid)
            total_price += offer.price
        total_items = len(cart)
    return total_price, total_items

@require_POST
def update_cart_item_view(request, offer_id):
    """ Met à jour la quantité d’une ligne :
    - action=inc  -> +1
    - action=dec  -> -1 (si qty arrive à 0 => supprime la ligne)
    - action=set  + quantity=<n> -> fixe la quantité à n (>=1)
    Retourne JSON : {ok, quantity, line_total, total_price, cart_count, removed} """
    action = request.POST.get("action")
    cart = _get_cart_dict(request)
    key = str(offer_id)
    qty = cart.get(key, 0)

    if action == "inc":
        qty += 1
    elif action == "dec":
        qty -= 1
    elif action == "set":
        try:
            qty = max(1, int(request.POST.get("quantity", "1")))
        except ValueError:
            qty = max(1, qty or 1)

    removed = False
    if qty <= 0:
        cart.pop(key, None)
        removed = True
    else:
        cart[key] = qty

    request.session['cart'] = cart
    request.session.modified = True

    # Calculs
    total_price, cart_count = _cart_totals(cart)
    line_total = 0
    if not removed:
        offer = get_object_or_404(Offer, id=offer_id)
        line_total = float(offer.price) * qty

    return JsonResponse({
        "ok": True,
        "quantity": qty if not removed else 0,
        "line_total": float(line_total),
        "total_price": float(total_price),
        "cart_count": cart_count,
        "removed": removed,
    })

@require_POST
def remove_from_cart_view(request, offer_id):
    """Supprime complètement la ligne d’article."""
    cart = _get_cart_dict(request)
    cart.pop(str(offer_id), None)
    request.session['cart'] = cart
    request.session.modified = True

    total_price, cart_count = _cart_totals(cart)
    return JsonResponse({
        "ok": True,
        "total_price": float(total_price), #float(...) dans le json pour éviter un éventuel souci de sérialisation de Decimal
        "cart_count": cart_count,
        "removed": True,
    })
