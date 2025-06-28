// Предотвращаем повторное объявление
if (typeof window.PostFormPricing !== 'undefined') {
    console.log('PostFormPricing уже загружен');
} else {
    console.log('PostFormPricing.js loaded');

class PostFormPricing {
    constructor() {
        this.init();
    }

    init() {
        // Выполнится один раз, когда скрипт загрузился
        this.bindAll();
    }

    bindAll() {
        // При первой загрузке страницы
        document.addEventListener('DOMContentLoaded', () => this.setupForm());
        
        // При показе Bootstrap модалки
        document.addEventListener('shown.bs.modal', (evt) => {
            console.log('Bootstrap модалка показана:', evt.target);
            this.setupForm();
        });

        // После любой подгрузки HTMX
        document.body.addEventListener('htmx:afterSwap', (evt) => {
            console.log('HTMX afterSwap событие:', evt.detail);
            // если в swap-обновлении была ваша форма
            if (evt.detail.target.closest('form[hx-post]') || 
                evt.detail.target.querySelector('form[hx-post]')) {
                console.log('Найдена форма после HTMX, запускаем setupForm');
                this.setupForm();
            }
        });
    }

    setupForm() {
        console.log('PostFormPricing: setupForm() вызван');
        const form = document.querySelector('form[hx-post]');
        if (!form) {
            console.log('PostFormPricing: форма не найдена');
            console.log('Все формы на странице:', document.querySelectorAll('form'));
            return;
        }
        console.log('PostFormPricing: инициализируем для формы', form);

        // Сохраняем референсы
        this.form            = form;
        this.submitBtn       = form.querySelector('#submit-btn');
        this.imageField      = form.querySelector('#image-field');
        this.pricingBreakdown= form.querySelector('#pricing-breakdown');
        this.addonsCheckboxes= Array.from(form.querySelectorAll('input[type=checkbox].pricing-addon'));
        
        console.log('PostFormPricing: найдены элементы:');
        console.log('  submitBtn:', this.submitBtn);
        console.log('  imageField:', this.imageField);
        console.log('  pricingBreakdown:', this.pricingBreakdown);
        console.log('  addonsCheckboxes:', this.addonsCheckboxes);

        // Убираем предыдущие слушатели (чтобы не дублировались)
        this.addonsCheckboxes.forEach(cb => cb.replaceWith(cb.cloneNode(true)));
        this.addonsCheckboxes = Array.from(form.querySelectorAll('input[type=checkbox].pricing-addon'));

        // Вешаем обработчики
        this.addonsCheckboxes.forEach(cb => cb.addEventListener('change', () => {
            console.log('PostFormPricing: чекбокс сменился', cb.name, cb.checked);
            this.toggleImageField();
            this.updatePricing();
        }));

        // Первоначальные действия
        this.toggleImageField();
        this.updatePricing();
    }

    toggleImageField() {
        const photoAddon = this.form.querySelector('input[name="addon_photo"]')?.checked;
        const imageInput = this.form.querySelector('input[name="image"]');
        if (!this.imageField || !imageInput) {
            console.log('PostFormPricing: imageField или imageInput не найдены');
            return;
        }
        if (photoAddon) {
            console.log('PostFormPricing: показываем поле изображения');
            this.imageField.style.display = 'block';
            imageInput.setAttribute('required', 'required');
        } else {
            console.log('PostFormPricing: прячем поле изображения');
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

        console.log('PostFormPricing: запрашиваем расчёт с', data);

        fetch('/api/pricing-calculator/?' + new URLSearchParams(data), {
            method: 'GET',
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        })
        .then(res => {
            if (!res.ok) throw new Error(res.status);
            return res.json();
        })
        .then(json => {
            console.log('PostFormPricing: пришёл ответ', json);
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

// Экспортируем класс и создаем экземпляр
window.PostFormPricing = PostFormPricing;
new PostFormPricing();

} // Закрываем if
