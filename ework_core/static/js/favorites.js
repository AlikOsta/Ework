document.addEventListener('DOMContentLoaded', function() {
    initFavoriteButtons();
});

document.addEventListener('htmx:afterSwap', function() {
    initFavoriteButtons();
});

function initFavoriteButtons() {
    const favoriteBtns = document.querySelectorAll('.favorite-btn:not(.initialized)');
    
    favoriteBtns.forEach(btn => {
        btn.classList.add('initialized');
        
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            const postId = this.dataset.postId;
            const isFavorite = this.dataset.isFavorite === 'true';
            
            // Визуальная обратная связь
            this.classList.add('clicked');
            setTimeout(() => {
                this.classList.remove('clicked');
            }, 100);
            
            // Отправляем запрос
            fetch(`/post/${postId}/favorite/`, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': getCSRFToken(),
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({})
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Network error: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    // Обновляем состояние кнопки
                    this.dataset.isFavorite = data.is_favorite.toString();
                    
                    const icon = this.querySelector('i');
                    if (data.is_favorite) {
                        // Добавлено в избранное
                        icon.textContent = 'favorite';
                        this.classList.remove('text-muted');
                        this.classList.add('text-danger');
                    } else {
                        // Удалено из избранного
                        icon.textContent = 'favorite_border';
                        this.classList.remove('text-danger');
                        this.classList.add('text-muted');
                        
                        // Если мы на странице избранного, скрываем карточку
                        if (window.location.pathname.includes('/favorites/')) {
                            const card = this.closest('.col');
                            if (card) {
                                card.style.transition = 'opacity 0.3s ease';
                                card.style.opacity = '0';
                                setTimeout(() => {
                                    card.remove();
                                    // Проверяем, остались ли карточки
                                    checkEmptyFavorites();
                                }, 300);
                            }
                        }
                    }
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Произошла ошибка при обновлении избранного. Пожалуйста, попробуйте еще раз.');
            });
        });
    });
}

// Функция для проверки пустого списка избранного
function checkEmptyFavorites() {
    const container = document.getElementById('products-container');
    const remainingCards = container.querySelectorAll('.col').length;
    
    if (remainingCards === 0) {
        // Создаем блок с сообщением о пустом списке
        const emptyBlock = document.createElement('div');
        emptyBlock.className = 'col-12';
        emptyBlock.innerHTML = `
            <div class="empty-favorites text-center py-5">
                <div class="empty-icon mb-3">
                    <i class="material-icons text-danger" style="font-size: 48px;">favorite_border</i>
                </div>
                <h5 class="mb-3 text-dark">Нет избранных объявлений</h5>
                <p class="text-muted mb-4">
                    Добавляйте понравившиеся объявления в избранное, чтобы быстро находить их позже
                </p>
                <a href="/" class="btn btn-primary d-flex justify-content-center align-items-center">
                    <i class="material-icons me-2">search</i>
                    Найти объявления
                </a>
            </div>
        `;
        container.appendChild(emptyBlock);
    }
}

// Функция для получения CSRF токена
function getCSRFToken() {
    // Сначала пробуем получить из мета-тега
    const metaToken = document.querySelector('meta[name="csrf-token"]');
    if (metaToken) {
        return metaToken.getAttribute('content');
    }
    
    // Если нет мета-тега, пробуем из cookie
    return getCookie('csrftoken');
}

// Функция для получения CSRF токена
function getCSRFToken() {
    // Сначала пробуем получить из мета-тега
    const metaToken = document.querySelector('meta[name="csrf-token"]');
    if (metaToken) {
        return metaToken.getAttribute('content');
    }
    
    // Если нет мета-тега, пробуем из cookie
    return getCookie('csrftoken');
}

// Функция для получения CSRF токена из cookies
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Экспортируем функцию для использования в других местах
window.initFavoriteButtons = initFavoriteButtons;
