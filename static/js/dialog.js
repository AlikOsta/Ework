;(function() {
    const modalElement = document.getElementById('modal');
    const modal = new bootstrap.Modal(modalElement);
    htmx.on('htmx:afterSwap', (e) => {
        if (e.detail.target.id === 'dialog') {
            modal.show();
        }
    });

    document.addEventListener('click', function(e) {
        const link = e.target.closest('[hx-get][data-bs-dismiss="modal"]');
        
        if (link) {
            e.preventDefault();
            const url = link.getAttribute('hx-get');
            const target = link.getAttribute('hx-target');
        
            modal.hide();

            modalElement.addEventListener('hidden.bs.modal', function handler() {
                modalElement.removeEventListener('hidden.bs.modal', handler);

                htmx.ajax('GET', url, { target: target });
            }, { once: true });
        }
    });
})();
