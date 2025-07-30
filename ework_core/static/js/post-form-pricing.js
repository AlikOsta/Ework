// Предотвращаем повторное объявление
if (typeof window.PostFormPricing !== 'undefined') {
    console.log('PostFormPricing уже загружен');
} else {
    console.log('PostFormPricing.js loaded');

    // шаг 1 Заполнение формы объявления
class PostFormPricing {
    constructor() {
        this.init();
    }

    init() {
        this.bindAll();
    }

    bindAll() {
        document.addEventListener('DOMContentLoaded', () => this.setupForm());
        document.addEventListener('shown.bs.modal', (evt) => {
            this.setupForm();
        });
        document.body.addEventListener('htmx:afterSwap', (evt) => {
            if (evt.detail.target.closest('form[hx-post]') || 
                evt.detail.target.querySelector('form[hx-post]')) {
                this.setupForm();
            }
        });
    }

    setupForm() {
        const form = document.querySelector('form[hx-post]');
        if (!form) {
            return;
        }
        this.form            = form;
        this.submitBtn       = form.querySelector('#submit-btn');
        this.imageField      = form.querySelector('#image-field');
        this.pricingBreakdown= form.querySelector('#pricing-breakdown');
        this.addonsCheckboxes= Array.from(form.querySelectorAll('input[type=checkbox].pricing-addon'));
        this.addonsCheckboxes.forEach(cb => cb.replaceWith(cb.cloneNode(true)));
        this.addonsCheckboxes = Array.from(form.querySelectorAll('input[type=checkbox].pricing-addon'));

        this.addonsCheckboxes.forEach(cb => cb.addEventListener('change', () => {
            this.toggleImageField();
            this.updatePricing();
        }));

        this.toggleImageField();
        this.updatePricing();
    }

    toggleImageField() {
        const photoAddon = this.form.querySelector('input[name="addon_photo"]')?.checked;
        const imageInput = this.form.querySelector('input[name="image"]');
        if (!this.imageField || !imageInput) {
            return;
        }
        if (photoAddon) {
            this.imageField.style.display = 'block';
            imageInput.setAttribute('required', 'required');
        } else {
            this.imageField.style.display = 'none';
            imageInput.value = '';
            imageInput.removeAttribute('required');
        }
    }

    updatePricing() {
        const data = {
            addon_photo: this.form.querySelector('input[name="addon_photo"]')?.checked || false,
            addon_highlight: this.form.querySelector('input[name="addon_highlight"]')?.checked || false,
            addon_auto_bump: this.form.querySelector('input[name="addon_auto_bump"]')?.checked || false,
        };

        fetch('/api/pricing-calculator/?' + new URLSearchParams(data), {
            method: 'GET',
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        })
        .then(res => {
            if (!res.ok) throw new Error(res.status);
            return res.json();
        })
        .then(json => {
            this.renderPricing(json.breakdown);
            this.renderButton(json.button);
        })
        .catch(err => console.error('PostFormPricing: ошибка расчёта', err));
    }

    renderPricing(b) {
        if (!this.pricingBreakdown) return;
        let html = '';
        if (b.is_free && b.can_post_free) {
            html = `<div class="alert alert-success">Бесплатная публикация</div>`;
        } else {
            html = `
                <div class="d-flex justify-content-between">
                    <span>Базовая:</span>
                    <span>${b.base_price} ${b.currency.symbol}</span>
                </div>`;
            for (let key in b.addons) {
                let addon = b.addons[key];
                if (addon.selected && addon.price) {
                    html += `
                        <div class="d-flex justify-content-between small text-muted">
                            <span>+ ${addon.description}</span>
                            <span>${addon.price} ${b.currency.symbol}</span>
                        </div>`;
                }
            }
            html += `
                <hr>
                <div class="d-flex justify-content-between fw-bold">
                    <span>Итого:</span>
                    <span>${b.total_price} ${b.currency.symbol}</span>
                </div>`;
        }
        this.pricingBreakdown.innerHTML = html;
    }

    renderButton(btn) {
        if (!this.submitBtn || !btn) return;
        this.submitBtn.textContent = btn.text;
        this.submitBtn.className = btn.class;
        this.submitBtn.dataset.action = btn.action;
    }
}

window.PostFormPricing = PostFormPricing;
new PostFormPricing();

} 
