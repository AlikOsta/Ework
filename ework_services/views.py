
from django.urls import reverse_lazy
from django.utils.translation import gettext as _

from .models import PostServices
from .forms import ServicesPostForm
from ework_post.views import BasePostCreateView, BasePostUpdateView


class ServicesPostCreateView(BasePostCreateView):
    model = PostServices
    form_class = ServicesPostForm
    template_name = 'services/post_services_form.html'

    def get_success_url(self):
        return reverse_lazy('core:home')
    
    
class ServicesPostUpdateView(BasePostUpdateView):
    model = PostServices
    form_class = ServicesPostForm
    template_name = 'services/post_services_form.html'
    success_message = _('Услуга успешно обновлена и отправлена на модерацию')
    
    # def get_form_kwargs(self):
    #     """Переопределяем чтобы не передавать category_slug"""
    #     kwargs = super(BasePostUpdateView, self).get_form_kwargs()  # Вызываем UpdateView напрямую
    #     kwargs['user'] = self.request.user
    #     return kwargs
    
    

    