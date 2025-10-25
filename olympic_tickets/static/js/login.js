(function () {
    const modal = document.getElementById('signin-modal');
    const openBtn = document.getElementById('open-signin');

    function openModal() {
    if (modal) modal.classList.add('is-open');
    }

    function closeModal() {
        if (modal) modal.classList.remove('is-open');
    }

    if (openBtn) openBtn.addEventListener('click', openModal);

    document.addEventListener('click', function (e) {
        if (e.target.matches('[data-close]')) {
            closeModal();
        }
    });

    // Si la vue renvoie open_signin=True (ex: erreur d'auth), on ouvre automatiquement
    if (window.__OPEN_SIGNIN__) {
        openModal();
    }

    // Option: fermer avec Échap
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') closeModal();
    });
})();