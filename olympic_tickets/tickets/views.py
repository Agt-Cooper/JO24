# Create your views here.

from django.core.cache import cache #pour le rate-limite a la connexion
from django.contrib import messages
from django.utils import timezone

from decimal import Decimal

from django.shortcuts import render, get_object_or_404, redirect
from .models import Offer, Order, Profile

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, authenticate#, get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.admin.views.decorators import staff_member_required
from django.urls import reverse
from .forms import SignupLoginForm #OfferForm en import local dans manage_offers_view, de cette façon l'import ne s'exécute qu'au moment où la fonction est appelée
from django.http import JsonResponse, HttpResponseBadRequest  #ajout du httpResponseBadRequest
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
    total = Decimal(0)  #ajout ancien total = 0

    #Supporte dict {id: qty} et ancien format liste
    if isinstance(cart, dict):
        for offer_id, qty in cart.items():
            offer = get_object_or_404(Offer, id=int(offer_id))
            line_total = offer.price * int(qty) # ajout ancien *qty
            items.append({'offer': offer, 'quantity': int(qty), 'line_total': line_total})  #ajout ancien 'quantity': qty
            total += line_total

    else:
        # ancien format: chaque id compte pour 1
        for offer_id in cart:
            offer = get_object_or_404(Offer, id=int(offer_id))  #ajout ancien id=offer_id
            line_total = offer.price
            items.append({'offer': offer, 'quantity': 1, 'line_total': line_total}) #ajout correction 'offer' était écrit offer
            total += line_total

    return render(request, 'tickets/cart.html', {'cart': items, 'total_price': total})

# Ajouter au panier
@require_POST
def add_to_cart_view(request, offer_id):
    #Valide l'offre (404 si inexistante)
    get_object_or_404(Offer, id=int(offer_id)) #ajout oublie mais ça ou id=offer_id
    # Récupère la quantité depuis le POST (>=1)
    try:
        qty = int(request.POST.get("quantity", "1"))
    except (TypeError, ValueError): #ajout ajout de TypeError
        qty = 1
    qty = max(1, qty)

    cart = request.session.get('cart', [])

    # Si l'ancien panier est une LISTE d'IDs → on la convertit en DICT {id: qty}
    if isinstance(cart, list):
        new_cart = {}
        for oid in cart:
            k= str(int(oid)) #ajout ancien k= str(oid)
            new_cart[k] = new_cart.get(k, 0) + 1
        cart = new_cart

    # Maintenant `cart` est un dict { "offer_id": qty }
    key = str(int(offer_id)) #ajout ancien str(offer_id)
    cart[key] = cart.get(key, 0) + qty  # doit ajouter la quantité choisie

    request.session['cart'] = cart
    request.session.modified = True

    # Requête AJAX → renvoie le compteur total (somme des quantités)
    is_ajax = (
            request.headers.get('x-requested-with') == 'XMLHttpRequest'
            or request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'
    )
    if is_ajax:
        total_items = sum(int(v) for v in cart.values())
        return JsonResponse({"ok": True, "cart_count": total_items, "added_qty": qty})

    return redirect(request.META.get("HTTP_REFERER") or '/')

# GESTION DES OFFRES (CRUD)

def _is_staff_or_superuser(user):
    """Test utilisé pour restreindre l’accès au CRUD."""
    return user.is_authenticated and (user.is_staff or user.is_superuser)

# Les deux vues suivantes concernent l'ajout suppression des quantités dans le panier

def _get_cart_dict(request):
    """Garantit que le panier est un dict {str(offer_id): qty}."""
    cart = request.session.get('cart', {})
    if isinstance(cart, list):
        # rétro-compatibilité
        d = {}
        for oid in cart:
            k = str(int(oid))
            d[k] = d.get(k, 0) + 1
        cart = d
    return cart

def _cart_totals(cart):
    """Calcule le total du panier et le nombre total d’articles."""
    total_items = sum(int(v) for v in cart.values()) if isinstance(cart, dict) else len(cart) #ajout ancien sum(cart.values()) if isinstance(cart, dict) else len(cart)
    total_price = Decimal(0) #ajout ancien 0
    if isinstance(cart, dict):
        for oid, qty in cart.items():
            offer = get_object_or_404(Offer, id=int(oid))
            total_price += offer.price * int(qty) #ajout ancien * qty
    else:
        for oid in cart:
            offer = get_object_or_404(Offer, id=int(oid)) #ajout ancien id=oid)
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
    if action not in {'inc', 'dec', 'set'}:
        return HttpResponseBadRequest("Action invalide")
    cart = _get_cart_dict(request)
    key =  str(int(offer_id)) #ajout ancien str(offer_id)
    qty = int(cart.get(key, 0)) #ajout ancien cart.get(key, 0)

    if action == 'inc':
        qty += 1
    elif action == 'dec':
        qty -= 1
    elif action == 'set':
        try:
            qty = max(1, int(request.POST.get("quantity", "1")))
        except (TypeError, ValueError): #ajout ancien ValueError:
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
    line_total = Decimal(0) #ajout ancien 0
    if not removed:
        offer = get_object_or_404(Offer, id=int(offer_id)) #ajout ancien id=offer_id)
        line_total = offer.price * qty #ajout ancien float(offer.price) * qty

    return JsonResponse({
        "ok": True,
        "quantity": qty if not removed else 0,
        "line_total": float(line_total), # cast safe pour JSON
        "total_price": float(total_price), # idem
        "cart_count": cart_count,
        "removed": removed,
    })

@require_POST
def remove_from_cart_view(request, offer_id):
    """Supprime complètement la ligne d’article."""
    cart = _get_cart_dict(request)
    cart.pop(str(int(offer_id)), None) #ajout ancien cart.pop(str(offer_id), None)
    request.session['cart'] = cart
    request.session.modified = True

    total_price, cart_count = _cart_totals(cart)
    return JsonResponse({
        "ok": True,
        "total_price": float(total_price), #float(...) dans le json pour éviter un éventuel souci de sérialisation de Decimal
        "cart_count": cart_count,
        "removed": True,
    })


def signup_login_view(request):
    """ Page 'Login' :
        - Prénom, Nom, Email, Mot de passe (+ confirmation)
        - Crée l’utilisateur, puis le connecte et redirige vers l’accueil
    """
    if request.method == "POST":
        form = SignupLoginForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"Bienvenue {user.first_name} ! Votre nom d'utilisateur est {user.username}.")
            login(request, user)
            next_url = request.POST.get("next") or request.GET.get("next") or reverse("home")
            return redirect(next_url)
    else:
        form = SignupLoginForm()
    return render(request, "tickets/login.html", {"form": form})

# Partie ajoutée pour le popup



def _rate_key(request, username: str) -> str:
    """
    Construit une clé de limitation par couple (IP, username).
    Utilise X-Forwarded-For si présent (cas proxy/CDN), sinon REMOTE_ADDR.
    """
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    ip = forwarded.split(",")[0].strip() if forwarded else request.META.get("REMOTE_ADDR", "unknown")
    uname_norm = (username or "").strip().lower()
    return f"signin_rate:{ip}:{uname_norm}"


def signin_view(request):
    """Connexion via *username* + mot de passe (utilisée par la modale)."""
    if request.method == "POST":
        username = (request.POST.get("username") or "").strip()
        password = request.POST.get("password") or ""
        next_url = request.POST.get("next") or request.GET.get("next") or reverse("home")

        # --- Rate limit : 5 tentatives / 15 minutes par (IP + username) ---
        key = _rate_key(request, username)
        data = cache.get(key) or {"count": 0, "first": timezone.now()}
        if data.get("count", 0) >= 5:
            from .forms import SignupLoginForm
            form = SignupLoginForm()
            ctx = {
                "form": form,
                "open_signin": True,
                "signin_error": "Trop de tentatives. Réessayez dans quelques minutes.",
            }
            return render(request, "tickets/login.html", ctx)

        # --- Authentification directe par username ---
        user = authenticate(request, username=username, password=password)
        if user:
            cache.delete(key)  # reset du compteur à la réussite
            login(request, user)
            return redirect(next_url)

        # --- Échec : incrémente et renvoie la modale ouverte avec message ---
        data["count"] = data.get("count", 0) + 1
        cache.set(key, data, timeout=15 * 60)

        from .forms import SignupLoginForm
        form = SignupLoginForm()
        ctx = {
            "form": form,
            "open_signin": True,
            "signin_error": "Nom d’utilisateur ou mot de passe invalide.",
        }
        return render(request, "tickets/login.html", ctx)

    # GET : affiche la page avec la modale disponible
    from .forms import SignupLoginForm
    form = SignupLoginForm()
    return render(request, "tickets/login.html", {"form": form})


@staff_member_required
def offers_manage_view(request):
    #exemple de rendu (adapte le template/ctx) à détailler
    """
        Page unique de gestion des offres :
        - GET : liste + formulaire (création ou édition si ?edit=<pk>)
        - POST : create / update / delete selon `action`
        """
    from .forms import OfferForm

    edit_id = request.GET.get("edit")
    offer_to_edit = None
    if edit_id:
        offer_to_edit = get_object_or_404(Offer, pk=int(edit_id))

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "create":
            form = OfferForm(request.POST)
            if form.is_valid():
                form.save()
                return redirect(reverse("offers_manage"))
        elif action == "update":
            offer_id = int(request.POST.get("offer_id"))
            offer = get_object_or_404(Offer, pk=offer_id)
            form = OfferForm(request.POST, instance=offer)
            if form.is_valid():
                form.save()
                return redirect(reverse("offers_manage"))
        elif action == "delete":
            offer_id = int(request.POST.get("offer_id"))
            offer = get_object_or_404(Offer, pk=offer_id)
            offer.delete()
            return redirect(reverse("offers_manage"))

        # action inconnue -> retour simple
        return redirect(reverse("offers_manage"))

    # GET
    form = OfferForm(instance=offer_to_edit) if offer_to_edit else OfferForm()
    offers = Offer.objects.order_by("name")

    return render(request, "tickets/offers_manage.html", {
        "offers": offers,
        "form": form,
        "is_editing": bool(offer_to_edit),
        "offer_being_edited": offer_to_edit,
    })
    #return render(request, "tickets/offers_manage.html", {"title": "Gestion des offres"})

#ajout pour le paiement
@login_required
def payment_start(request, order_id):
    '''
    page mock de paiement avec le récap et le bouton pour achat
    (ordre en pending et en attente de l'utilisateur)
    '''
    order = get_object_or_404(Order, pk=order_id, user=request.user, status="pending")
    return render(request,'tickets/payment_start.html', {
        "order": order,
    })

@login_required
def payment_confirm(request, order_id: int):
    '''
    simule le payement. on aura une clé 2 pour chate offre
    ensuite la commande passe en payé, puis on est redirigé vers mes achats
    '''
    if request.method != "POST": #on force la confirmation ce qui évite la génération de la clé directement
        return redirect(reverse("payment_start", args=(order_id,)))
    order = get_object_or_404(Order, pk=order_id, user=request.user, status="pending")

    signup_key = getattr(request.user, "profile", None)
    if not signup_key or not signup_key.signup_key:  #si profil sans clé1 alors pas de statut payé
        return render(request, "tickets/payment_start.html", {
            "order": order,
            "error": "Impossible de générer le billet car la clé est manquante."
        })
    #gén!re un billet par ligne
    for item in order.items.all():
        item.generate_ticket(request.user.profile.signup_key)

    # statut payé
    order.status = "paid"
    order.save(update_fields=["status"])

    return redirect("my_purchases")

@login_required
def my_purchases(request):
    #liste des commandes payés avec les billets
    orders = Order.objects.filter(user=request.user, status="paid").prefetch_related("items", "items__offer")
    #Il faut éviter de faire la logique QR dans l'HTML, c'est mieux de faire ça pour le template
    orders_with_qr = []
    for order in orders:
        items = []
        for it in order.items.all():
            items.append({
                "offer": it.offer,
                "quantity": it.quantity,
                "unit_price": it.unit_price,
                "final_ticket_key": it.final_ticket_key,
                "qr_data": it.qr_data_uri(), #None si pas encore payéou généré
            })
        orders_with_qr.append({"order": order, "items": items})
    return render(request, "tickets/my_purchases.html", {"orders": orders_with_qr})