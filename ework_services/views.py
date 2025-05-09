from django.urls import reverse_lazy
from ework_post.views import (
    BasePostListView, 
    BasePostDetailView, 
    BasePostCreateView, 
    BasePostUpdateView, 
    BasePostDeleteView, 
    base_toggle_favorite,
)
from .models import PostServices, FavoriteServices, ProductViewServices
from .forms import ServicePostForm
from ework_rubric.models import SubRubric



class ServiceListView(BasePostListView):
    model = PostServices
    category_model = SubRubric
    template_name = 'services/service_list.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Услуги'
        return context


class ServiceDetailView(BasePostDetailView):
    model = PostServices
    favorite_model = FavoriteServices
    view_model = ProductViewServices
    template_name = 'services/service_detail.html'


class ServiceCreateView(BasePostCreateView):
    model = PostServices
    form_class = ServicePostForm
    template_name = 'services/service_form.html'
    success_url = reverse_lazy('services:service_list')


class ServiceUpdateView(BasePostUpdateView):
    model = PostServices
    form_class = ServicePostForm
    template_name = 'services/service_form.html'


class ServiceDeleteView(BasePostDeleteView):
    model = PostServices
    template_name = 'services/service_confirm_delete.html'
    success_url = reverse_lazy('services:service_list')


def toggle_service_favorite(request, pk):
    """Добавление/удаление услуги из избранного"""
    return base_toggle_favorite(request, pk, FavoriteServices, PostServices)