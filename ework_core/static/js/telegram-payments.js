
class TelegramPayments {
    constructor() {
        this.initWebApp();
        this.setupFormHandlers();
    }

    initWebApp() {
        if (typeof window.Telegram !== 'undefined' && window.Telegram.WebApp) {
            this.tg = window.Telegram.WebApp;
            this.tg.ready();
            this.tg.expand();
        } else {
            console.warn('TelegramPayments: Telegram WebApp недоступен');
            this.tg = null;
        }
    }

    setupFormHandlers() {
        // Обработчик для HTMX ответов с платежом
        document.body.addEventListener('htmx:afterRequest', (event) => {
            const xhr = event.detail.xhr;
            
            if (event.detail.target.matches('form[hx-post]')) {
                try {
                    const response = JSON.parse(xhr.responseText);
                    
                    if (response.action === 'payment_required') {
                        this.openPayment(response);
                    }
                } catch (e) {
                    console.error('TelegramPayments: ошибка обработки ответа', e);
                }
            }
        });
    }

    async openPayment(paymentData) {
        if (!this.tg) {
            alert('Платежи доступны только в Telegram');
            return;
        }

        try {
            // Создаем инвойс на сервере
            const response = await fetch('/api/create-invoice/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    payment_id: paymentData.payment_id,
                    amount: paymentData.amount
                })
            });

            const result = await response.json();
            
            if (result.success && result.invoice_link) {
                
                // Открываем платеж через Telegram WebApp
                this.tg.openInvoice(result.invoice_link, (status) => {
                    
                    if (status === 'paid') {
                        this.showSuccess();
                        setTimeout(() => window.location.reload(), 200);
                    } else {
                        alert('Оплата не была завершена');
                    }
                });
            } else {
                throw new Error(result.error || 'Ошибка создания счета');
            }
            
        } catch (error) {
            console.error('TelegramPayments: ошибка', error);
            alert('Ошибка: ' + error.message);
        }
    }

    showSuccess() {
        const form = document.querySelector('form[hx-post]');
        if (form) {
            form.innerHTML = `
                <div class="alert alert-success text-center">
                    <h5>✅ Оплата успешна!</h5>
                    <p>Ваше объявление опубликовано</p>
                </div>
            `;
        }
    }

    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    }
}

// Инициализируем только если еще не инициализировано
if (typeof window.telegramPayments === 'undefined') {
    window.telegramPayments = new TelegramPayments();
    console.log('TelegramPayments инициализирован');
}
