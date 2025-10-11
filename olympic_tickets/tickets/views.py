# Create your views here.
import profile

from django.core.mail import send_mail
from .tokens import make_email_token, read_email_token
from django.core.cache import cache #pour le rate-limite signin
from django.contrib import messages
from django.utils import timezone

from decimal import Decimal

from django.shortcuts import render, get_object_or_404, redirect
from .models import Offer, Profile

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, authenticate, get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
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

    # Si ton ancien panier est une LISTE d'IDs → on la convertit en DICT {id: qty}
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

    # # Requête AJAX → renvoie le compteur total (somme des quantités)
    # if request.headers.get('x-requested-with') == 'XMLHttpRequest':
    #     total_items = sum(cart.values()) # PLUS UTILE ?? if isinstance(cart, dict) else len(cart)
    #     return JsonResponse({"ok": True, "cart_count": total_items, "added_qty": qty})

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
        offer_to_edit = get_object_or_404(Offer, pk=int(edit_id)) #ajout ancien pk=edit_id)

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "create":
            form = OfferForm(request.POST)
            if form.is_valid():
                form.save()
                return redirect(reverse("offers_manage"))

        elif action == "update":
            offer_id = request.POST.get("offer_id")
            offer = get_object_or_404(Offer, pk=int(offer_id)) #ajout ancien pk=offer_id)
            form = OfferForm(request.POST, instance=offer)
            if form.is_valid():
                form.save()
                return redirect(reverse("offers_manage"))

        elif action == "delete":
            offer_id = request.POST.get("offer_id")
            offer = get_object_or_404(Offer, pk=int(offer_id)) #ajout ancien pk=offer_id)
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
            k = str(int(oid))
            d[k] = d.get(k, 0) + 1
            #ajout ancien d[str(oid)] = d.get(str(oid), 0) + 1 ET pas les deux lignes du dessus
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


#Partie mail de vérification
def _send_verify_email(request, user):
    token = make_email_token(user)
    verify_url = request.build_absolute_uri(reverse("verify_email") + f"?token={token}")
    subject = "Validez votre email - JO 2024"
    message = (
        f"Bonjour {user.first_name},\n\n"
        f"Merci de créer un compte, Pour vérifier votre email, cliquez sur le lien :\n{verify_url}\n\n"
        "Ce lien expire dans 3 jours."
    )
    send_mail(subject, message, None, [user.email], fail_silently=False)

def signup_login_view(request):
    """ Page 'Login' transformée en inscription :
        - Prénom, Nom, Email, Mot de passe (+ confirmation)
        - Crée l’utilisateur, puis le connecte et redirige vers l’accueil
    """
    if request.method == "POST":
        form = SignupLoginForm(request.POST)
        if form.is_valid():
            user = form.save()
            _send_verify_email(request, user) #envoie le mail de vérification
            login(request, user)
            return redirect("home")
    else:
        form = SignupLoginForm()
    return render(request, "tickets/login.html", {"form": form})

# Partie ajoutée pour le popup

def signin_view(request):
    """Connexion via e-mail + mot de passe (utilisée par la modale)."""
    if request.method == "POST":
        email = (request.POST.get("email") or "").strip().lower()
        password = request.POST.get("password") or ""
        next_url = request.POST.get("next") or request.GET.get("next") or reverse("home")

        # RateLimit: 5 tentives par 15min par (ip+email)
        key = _rate_key(request, email)
        data = cache.get(key) or {"count": 0, "first" : timezone.now()}
        if data["count"] >= 5:
            from .forms import SignupLoginForm
            form = SignupLoginForm()
            ctx = {"form": form, "open_signin": True, "signin_error": "Trop de tentatives. Réessayer dans quelques minutes",
            }
            return render(request, "tickets/login.html", ctx)

        #Auth
        User = get_user_model()
        user_obj = User.objects.filter(email__iexact=email).first()
        user = None
        if user_obj:
            # NB: username = user_obj.username (si AUTH_USER_MODEL personnalisé, adapter)
            user = authenticate(request, username=user_obj.username, password=password)
        if user:
            cache.delete(key) #sert a reset la fenetre
            login(request, user)
            return redirect(next_url)
        else:
            data["count"] += 1
            cache.set(key, data, timeout=15 * 60) #15min
            from .forms import SignupLoginForm
            form = SignupLoginForm
            ctx = {
                "form": form,
                "open_signin": True,
                "signin_error": "Email ou mot de passe invalide.",
            }
            return render(request, "tickets/login.html", ctx)

    return redirect("login")
#ajouté pour aller avec le signin_view
def _rate_key(request, email):
    ip = request.META.get("REMOTE_ADDR", "ip-unknown")
    return f"signin:{ip}:{email.lower()}"

#Pour la vérification par email
@login_required
def verify_email_view(request):
    token = request.GET.get("token")
    if not token:
        messages.error(request, "Lien de vérification invalide.")
        return redirect("home")

    user_id, email = read_email_token(token)
    if not user_id or user_id != request.user.id or email.lower() != request.user.email.lower():
        messages.error(request, "Lien de vérification invalide ou expiré.")
        return redirect("home")

    profile = Profile.objects.get(user=request.user)
    if not profile.email_verified:
        profile.email_verified = True
        profile.save()
        messages.success(request, "Votre adresse email a été vérifiée. Merci !")
    else:
        messages.info(request, "Votre adresse email était déjà vérifiée.")
    return redirect("home")

#pour le renvoie de mail
@login_required
def resend_verify_email_view(request):
    # Si déjà vérifié, inutile
    profile = Profile.objects.get(user=request.user)
    if profile.email_verified:
        messages.info(request, "Votre e-mail est déjà vérifié.")
        return redirect("home")

    # Anti-spam : 1 envoi max toutes les 5 minutes
    key = f"resend_verify:{request.user.id}"
    last_ts = cache.get(key)
    if last_ts:
        messages.warning(request, "Vous avez déjà demandé un envoi récemment. Réessayez dans quelques minutes.")
        return redirect("home")

    # Envoi
    _send_verify_email(request, request.user)
    messages.success(request, "Un nouveau lien de vérification vous a été envoyé par e-mail.")

    # Pose un verrou de 5 minutes
    cache.set(key, timezone.now().timestamp(), timeout=5*60)
    return redirect("home")