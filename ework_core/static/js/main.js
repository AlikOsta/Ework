// const triggerTabList = document.querySelectorAll('#myTab a')
// triggerTabList.forEach(triggerEl => {
//   const tabTrigger = new bootstrap.Tab(triggerEl)

//   triggerEl.addEventListener('click', event => {
//     event.preventDefault()
//     tabTrigger.show()
//   })
// })


// document.addEventListener('DOMContentLoaded', function() {
//     const firstTab = document.querySelector('#myTab .nav-link.active');
//     if (firstTab) {
//         htmx.trigger(firstTab, 'click');
//     }
// });


function activateTab(tabElement, url) {
    document.querySelectorAll('#myTab .nav-link').forEach(tab => {
        tab.classList.remove('active');
    });
    tabElement.classList.add('active');
    htmx.ajax('GET', url, {target: '#content-area'});
    return false;
}


document.addEventListener('DOMContentLoaded', function() {
    const firstTab = document.querySelector('#myTab .nav-link');
    if (firstTab) {
        const url = firstTab.getAttribute('data-url');
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
