from django.shortcuts import render, get_object_or_404, redirect
from django.utils.translation import gettext_lazy as _
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required

class BasePostListView(ListView):
    """Базовое представление для списка объявлений"""
    template_name = 'post/post_list.html'
    context_object_name = 'posts'
    
    def get_queryset(self):
        queryset = self.model.objects.filter(status=3)
        
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) | 
                Q(description__icontains=search_query)
            )

        category_slug = self.kwargs.get('category_slug')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = self.category_model.objects.all()
        
        search_query = self.request.GET.get('q')
        if search_query:
            context['search_query'] = search_query
            
        return context


@login_required
class BasePostDetailView(DetailView):
    """Базовое представление для детальной страницы объявления"""
    template_name = 'post/post_detail.html'
    context_object_name = 'post'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        post = self.get_object()
        similar_posts = self.model.objects.filter(
            category=post.category, 
            status=3
        ).exclude(id=post.id)[:4]
        
        context['similar_posts'] = similar_posts
        
        if self.request.user.is_authenticated:
            context['is_favorite'] = self.favorite_model.objects.filter(
                user=self.request.user,
                product=post
            ).exists()
            
        return context
    
    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        
        if request.user.is_authenticated:
            post = self.get_object()
            self.view_model.objects.get_or_create(
                user=request.user,
                product=post
            )
            
        return response


@login_required
class BasePostCreateView(LoginRequiredMixin, CreateView):
    """Базовое представление для создания объявления"""
    template_name = 'post/post_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.status = 0 
        messages.success(self.request, _('Объявление успешно создано и отправлено на модерацию'))
        return super().form_valid(form)


@login_required
class BasePostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Базовое представление для редактирования объявления"""
    template_name = 'post/post_form.html'
    
    def test_func(self):
        post = self.get_object()
        return self.request.user == post.user
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        form.instance.status = 0 
        messages.success(self.request, _('Объявление успешно обновлено и отправлено на модерацию'))
        return super().form_valid(form)


@login_required
class BasePostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Базовое представление для удаления объявления"""
    template_name = 'post/post_confirm_delete.html'
    
    def test_func(self):
        post = self.get_object()
        return self.request.user == post.user
    
    def get_success_url(self):
        messages.success(self.request, _('Объявление успешно удалено'))
        return reverse_lazy('profile')


@login_required
@require_POST
def base_toggle_favorite(request, pk, favorite_model, post_model):
    """Базовая функция для добавления/удаления из избранного"""
    post = get_object_or_404(post_model, pk=pk)
    
    favorite, created = favorite_model.objects.get_or_create(
        user=request.user,
        product=post
    )
    
    if not created:
        favorite.delete()
        is_favorite = False
    else:
        is_favorite = True
    
    return JsonResponse({
        'success': True,
        'is_favorite': is_favorite
    })