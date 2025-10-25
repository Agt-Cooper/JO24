def cart_count(request):
    cart = request.session.get('cart', [])
    if isinstance(cart, dict):
        return {"cart_count": sum(cart.values())}
    # ancien format: liste d'IDs
    return {"cart_count": len(cart)}