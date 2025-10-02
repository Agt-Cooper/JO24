function updateCartCount(n) {
    const el = document.getElementById('cart-count');
    if (el) el.textContent = `(${n})`;
}

document.addEventListener('DOMContentLoaded', function () {
    document.body.addEventListener('submit', async function (e) {
    const form = e.target.closest('.add-to-cart-form');
    if (!form) return;

    e.preventDefault();

    const csrfInput = form.querySelector('input[name=csrfmiddlewaretoken]');
    const csrf = csrfInput ? csrfInput.value : '';
    const action = form.getAttribute('action');

    try {
        const resp = await fetch(action, {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': csrf,
        },
        body: new FormData(form),
        });

        if (!resp.ok) throw new Error('HTTP ' + resp.status);
        const data = await resp.json();

        if (data.ok) {
        updateCartCount(data.cart_count);
        // Feedback visuel rapide (optionnel)
        const btn = form.querySelector('button');
        btn?.classList.add('added');
        setTimeout(() => btn?.classList.remove('added'), 500);
        }
    } catch (err) {
        console.error('Erreur add-to-cart:', err);
      // Fallback: on soumet "vraiment" le formulaire si AJAX échoue
        // form.submit();
    }
    });
});
