function activateTab(tabElement, url) {
    document.querySelectorAll('#myTab .nav-link').forEach(tab => {
        tab.classList.remove('active');
    });
    tabElement.classList.add('active');
    const searchInput = document.querySelector('input[name="q"]');
    if (searchInput) {
        searchInput.value = '';
        const clearBtn = document.getElementById('clear-search-btn');
        if (clearBtn) clearBtn.style.display = 'none';
    }
    const rubricId = tabElement.getAttribute('data-category-id');
    const searchForm = document.getElementById('search-form');
    if (searchForm) {
        searchForm.setAttribute('data-active-rubric', rubricId);
        const rubricIdInput = document.getElementById('search-rubric-id');
        if (rubricIdInput) rubricIdInput.value = rubricId;
    }

    htmx.ajax('GET', url, {target: '#content-area'});

    return false;
}

document.addEventListener('DOMContentLoaded', function() {
    // Добавляем обработчики событий для табов
    document.querySelectorAll('#myTab .nav-link').forEach(tab => {
        tab.addEventListener('click', function(e) {
            e.preventDefault();
            const url = this.getAttribute('data-url');
            activateTab(this, url);
        });
    });

    // Загружаем контент для активного таба
    const activeTab = document.querySelector('#myTab .nav-link.active');
    if (activeTab) {
        const rubricId = activeTab.getAttribute('data-category-id');
        const searchForm = document.getElementById('search-form');
        if (searchForm) {
            searchForm.setAttribute('data-active-rubric', rubricId);
        }
        const url = activeTab.getAttribute('data-url');
        htmx.ajax('GET', url, {target: '#content-area'});
    }
});

document.body.addEventListener('htmx:afterSwap', function(evt) {
    if (evt.detail.target.id === 'main-content' && 
        (evt.detail.xhr.responseURL.endsWith('/') || 
         evt.detail.xhr.responseURL.includes('/home'))) {
        const activeTab = document.querySelector('#myTab .nav-link.active');
        if (activeTab) {
            const url = activeTab.getAttribute('data-url');
            htmx.ajax('GET', url, {target: '#content-area'});
        } else {
            const firstTab = document.querySelector('#myTab .nav-link');
            if (firstTab) {
                firstTab.classList.add('active');
                const url = firstTab.getAttribute('data-url');
                htmx.ajax('GET', url, {target: '#content-area'});
            }
        }
    }
});
