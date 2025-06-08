from django.utils.translation import gettext_lazy as _
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from ework_post.models import AbsPost, Favorite
from ework_rubric.models import SuperRubric, SubRubric


class BasePostListView(ListView):
    """Базовое представление для списка объявлений"""
    model = AbsPost
    template_name = 'partials/post_list.html'
    context_object_name = 'posts'
    
    def get_queryset(self):
        queryset = self.model.objects.filter(status=3)
        
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) | 
                Q(description__icontains=search_query)
            )

        # Фильтрация по рубрике (если указана)
        rubric_pk = self.kwargs.get('rubric_pk')
        if rubric_pk:
            super_rubric = get_object_or_404(SuperRubric, pk=rubric_pk)
            sub_rubrics = SubRubric.objects.filter(super_rubric=super_rubric)
            sub_ids = sub_rubrics.values_list('id', flat=True)
            queryset = queryset.filter(sub_rubric_id__in=sub_ids)
        
        # Фильтрация по подрубрике (если указана)
        sub_rubric_pk = self.kwargs.get('sub_rubric_pk')
        if sub_rubric_pk:
            queryset = queryset.filter(sub_rubric_id=sub_rubric_pk)
            
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Добавляем избранные посты
        if self.request.user.is_authenticated:
            favorite_post_ids = Favorite.objects.filter(
                user=self.request.user, 
                post__in=context['posts']
            ).values_list('post_id', flat=True)
            context['favorite_post_ids'] = favorite_post_ids
        
        # Добавляем категории в зависимости от параметров
        rubric_pk = self.kwargs.get('rubric_pk')
        if rubric_pk:
            super_rubric = get_object_or_404(SuperRubric, pk=rubric_pk)
            context['categories'] = SubRubric.objects.filter(super_rubric=super_rubric)
        else:
            context['categories'] = SuperRubric.objects.all()
        
        # Добавляем поисковый запрос, если есть
        search_query = self.request.GET.get('q')
        if search_query:
            context['search_query'] = search_query
            
        return context


class BasePostCreateView(LoginRequiredMixin, CreateView):
    """Базовое представление для создания объявления"""
    template_name = 'post/post_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.user = self.request.user
        self.object.save()
            
        return super().form_valid(form)


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


