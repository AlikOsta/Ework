const triggerTabList = document.querySelectorAll('#myTab a')
triggerTabList.forEach(triggerEl => {
  const tabTrigger = new bootstrap.Tab(triggerEl)

  triggerEl.addEventListener('click', event => {
    event.preventDefault()
    tabTrigger.show()
  })
})


document.addEventListener('DOMContentLoaded', function() {

    const firstTab = document.querySelector('#myTab .nav-link.active');
    if (firstTab) {
        htmx.trigger(firstTab, 'click');
    }
});
