(function(){
            const csrftoken = (function(){
            const f = document.getElementById('csrf-form');
            const i = f ? f.querySelector('input[name=csrfmiddlewaretoken]') : null;
            return i ? i.value : '';
            })();

        function updateHeaderCount(n){
            const el = document.getElementById('cart-count');
            if (el) el.textContent = `(${n})`;
        }

        function setLine(offerId, qty, lineTotal){
            const qtyInput = document.getElementById('qty-' + offerId);
            if (qtyInput) qtyInput.value = qty;
            const lineEl = document.getElementById('line-' + offerId);
            if (lineEl) lineEl.textContent = lineTotal.toFixed(2) + ' €';
        }

        function setTotal(total){
            const totalEl = document.getElementById('total-price');
            if (totalEl) totalEl.textContent = total.toFixed(2);
        }

        async function postUpdate(url, data){
            const resp = await fetch(url, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': csrftoken,
                },
                body: data instanceof FormData ? data : new URLSearchParams(data),
            });

            if (!resp.ok) throw new Error('HTTP ' + resp.status);
            return await resp.json();
        }

      // Boutons + / −
            document.addEventListener('click', async function(e){
                const btn = e.target.closest('.qty-btn');
                if (!btn) return;
                const offerId = btn.getAttribute('data-offer-id');
                const action = btn.getAttribute('data-action');

                try {
                    const data = await postUpdate(`/cart/update/${offerId}/`, {action});
                    if (data.removed){
                // supprimer la ligne du DOM
                        const row = document.getElementById('row-' + offerId);
                        row && row.remove();
                    } else {
                        setLine(offerId, data.quantity, data.line_total);
                    }
                    setTotal(data.total_price);
                    updateHeaderCount(data.cart_count);
                } catch(err){
                    console.error(err);
                    alert("Erreur de mise à jour du panier.");
                }
            });

      // Modification quantité par saisie directe
        document.addEventListener('change', async function(e){
            const input = e.target.closest('.qty-input');
            if (!input) return;
            const offerId = input.id.replace('qty-','');
            const val = parseInt(input.value || '1', 10);
            const quantity = isNaN(val) ? 1 : Math.max(1, val);

            try {
                const data = await postUpdate(`/cart/update/${offerId}/`, {action:'set', quantity});
                if (data.removed){
                    const row = document.getElementById('row-' + offerId);
                    row && row.remove();
                } else {
                    setLine(offerId, data.quantity, data.line_total);
                }
                setTotal(data.total_price);
                updateHeaderCount(data.cart_count);
            } catch(err){
                console.error(err);
                alert("Erreur de mise à jour du panier.");
            }
        });

      // Bouton Supprimer
        document.addEventListener('click', async function(e){
            const btn = e.target.closest('.remove-btn');
            if (!btn) return;
            const offerId = btn.getAttribute('data-offer-id');

            if (!confirm('Supprimer cet article du panier ?')) return;

            try {
                const data = await postUpdate(`/cart/remove/${offerId}/`, {});
                const row = document.getElementById('row-' + offerId);
                row && row.remove();
                setTotal(data.total_price);
                updateHeaderCount(data.cart_count);
            } catch(err){
                console.error(err);
                alert("Erreur lors de la suppression.");
            }
        });
        })();