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

    for offer_id in cart:
        offer = get_object_or_404(Offer, id=offer_id)
        items.append({'offer': offer})
        total += offer.price

    return render(request, 'tickets/cart.html', {'cart': items, 'total_price': total})

# Ajouter au panier
@require_POST
def add_to_cart_view(request, offer_id):
    # on force une liste de strings ou ints, peu importe, mais on ré-écrit la session
    cart = request.session.get('cart', [])
    if offer_id not in cart:
        cart.append(offer_id)
    request.session['cart'] = cart #ecriture explicite
    request.session.modified = True #sécrutié: marque la session modifié

    # Si requête AJAX → on renvoie du JSON avec le nouveau compteur
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({"ok": True, "cart_count": len(cart)})

    # Fallback non-AJAX : revenir à la page précédente si possible
    next_url = request.META.get("HTTP_REFERER") or '/'
    return redirect(next_url)
# def add_to_cart_view(request, offer_id):
#     cart = request.session.get('cart', [])
#     cart.append(offer_id)
#     request.session['cart'] = cart
#     return redirect('cart')  A supprimer apres test


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