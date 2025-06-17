from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError

from ework_post.models import AbsPost, Favorite, PostView
from ework_rubric.models import SuperRubric, SubRubric


class PostViewMixin:
    """Миксин для записи просмотров постов"""
    
    def record_view(self, post, user):
        """Записать просмотр поста пользователем"""
        if not user.is_authenticated:
            return False
            
        if post.user == user:
            return False
            
        content_type = ContentType.objects.get_for_model(post)
        view_obj, created = PostView.objects.get_or_create(
            user=user,
            content_type=content_type,
            object_id=post.pk,
            defaults={'created_at': timezone.now()}
        )
        return created
    
    def get_view_count(self, post):
        """Получить количество просмотров поста"""
        content_type = ContentType.objects.get_for_model(post)
        return PostView.objects.filter(
            content_type=content_type,
            object_id=post.pk
        ).count()
    
    def get_user_views(self, user, post_queryset=None):
        """Получить просмотры пользователя"""
        views = PostView.objects.filter(user=user)
        if post_queryset is not None:
            content_types = ContentType.objects.get_for_models(
                *[type(post) for post in post_queryset]
            ).values()
            views = views.filter(content_type__in=content_types)
        return views


class FavoriteMixin:
    """Миксин для работы с избранными постами"""
    
    def toggle_favorite(self, post, user):
        """Переключить статус избранного для поста"""
        if not user.is_authenticated:
            return False, False
            
        favorite, created = Favorite.objects.get_or_create(
            user=user,
            post=post
        )
        
        if not created:
            favorite.delete()
            return False, True  # removed, action_performed
        
        return True, True  # added, action_performed
    
    def is_favorite(self, post, user):
        """Проверить, находится ли пост в избранном у пользователя"""
        if not user.is_authenticated:
            return False
        return Favorite.objects.filter(user=user, post=post).exists()
    
    def get_favorite_post_ids(self, user, post_queryset):
        """Получить ID избранных постов из queryset"""
        if not user.is_authenticated:
            return []
        return list(Favorite.objects.filter(
            user=user,
            post__in=post_queryset
        ).values_list('post_id', flat=True))


class PostFilterMixin:
    """Миксин для фильтрации постов"""
    
    def apply_search_filter(self, queryset, search_query):
        """Применить поисковый фильтр"""
        if search_query:
            return queryset.filter(
                Q(title__icontains=search_query) | 
                Q(description__icontains=search_query)
            )
        return queryset
    
    def apply_rubric_filter(self, queryset, rubric_pk=None, sub_rubric_pk=None):
        """Применить фильтр по рубрикам"""
        if sub_rubric_pk:
            return queryset.filter(sub_rubric_id=sub_rubric_pk)
        elif rubric_pk:
            super_rubric = get_object_or_404(SuperRubric, pk=rubric_pk)
            sub_rubrics = SubRubric.objects.filter(super_rubric=super_rubric)
            sub_ids = sub_rubrics.values_list('id', flat=True)
            return queryset.filter(sub_rubric_id__in=sub_ids)
        return queryset
    
    def apply_price_filter(self, queryset, price_min=None, price_max=None):
        """Применить фильтр по цене"""
        if price_min and price_min.isdigit():
            queryset = queryset.filter(price__gte=int(price_min))
        if price_max and price_max.isdigit():
            queryset = queryset.filter(price__lte=int(price_max))
        return queryset
    
    def apply_location_filter(self, queryset, city_id=None):
        """Применить фильтр по городу"""
        if city_id and city_id.isdigit():
            return queryset.filter(city_id=city_id)
        return queryset
    
    def apply_sorting(self, queryset, sort_type='newest'):
        """Применить сортировку"""
        sort_options = {
            'newest': '-created_at',
            'oldest': 'created_at',
            'price_asc': 'price',
            'price_desc': '-price',
            'premium': ['-is_premium', '-created_at'],
        }
        
        sort_fields = sort_options.get(sort_type, '-created_at')
        if isinstance(sort_fields, list):
            return queryset.order_by(*sort_fields)
        return queryset.order_by(sort_fields)


class BasePostListView(ListView, PostFilterMixin, FavoriteMixin):
    """Базовое представление для списка объявлений"""
    model = AbsPost
    template_name = 'partials/post_list.html'
    context_object_name = 'posts'
    paginate_by = 20
    
    def get_queryset(self):
        """Получить отфильтрованный queryset постов"""
        # Базовый queryset - только опубликованные и не удаленные посты
        queryset = self.model.objects.filter(
            status=3,  # Опубликовано
            is_deleted=False
        ).select_related('user', 'city', 'currency', 'sub_rubric')
        
        # Применяем фильтры
        search_query = self.request.GET.get('q')
        queryset = self.apply_search_filter(queryset, search_query)
        
        # Фильтрация по рубрикам
        rubric_pk = self.kwargs.get('rubric_pk')
        sub_rubric_pk = self.kwargs.get('sub_rubric_pk')
        queryset = self.apply_rubric_filter(queryset, rubric_pk, sub_rubric_pk)
        
        # Фильтрация по цене
        price_min = self.request.GET.get('price_min')
        price_max = self.request.GET.get('price_max')
        queryset = self.apply_price_filter(queryset, price_min, price_max)
        
        # Фильтрация по городу
        city_id = self.request.GET.get('city')
        queryset = self.apply_location_filter(queryset, city_id)
        
        # Сортировка
        sort_type = self.request.GET.get('sort', 'newest')
        queryset = self.apply_sorting(queryset, sort_type)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Добавляем избранные посты
        if self.request.user.is_authenticated:
            context['favorite_post_ids'] = self.get_favorite_post_ids(
                self.request.user, 
                context['posts']
            )
        else:
            context['favorite_post_ids'] = []
        
        # Добавляем категории в зависимости от параметров
        rubric_pk = self.kwargs.get('rubric_pk')
        if rubric_pk:
            super_rubric = get_object_or_404(SuperRubric, pk=rubric_pk)
            context['categories'] = SubRubric.objects.filter(super_rubric=super_rubric)
            context['current_rubric'] = super_rubric
        else:
            context['categories'] = SuperRubric.objects.all()
        
        # Добавляем параметры фильтрации для сохранения состояния
        context.update({
            'search_query': self.request.GET.get('q', ''),
            'price_min': self.request.GET.get('price_min', ''),
            'price_max': self.request.GET.get('price_max', ''),
            'selected_city': self.request.GET.get('city', ''),
            'sort': self.request.GET.get('sort', 'newest'),
        })
            
        return context


class BasePostDetailView(DetailView, PostViewMixin, FavoriteMixin):
    """Базовое представление для детального просмотра поста"""
    model = AbsPost
    template_name = 'post/post_detail.html'
    context_object_name = 'post'

    def get_queryset(self):
        """Получить queryset с оптимизированными связями"""
        return AbsPost.objects.select_related(
            'user', 'city', 'currency', 'sub_rubric', 'sub_rubric__super_rubric'
        ).filter(
            status=3, 
            is_deleted=False 
        )

    def get_object(self, queryset=None):
        """Получить объект и записать просмотр"""
        obj = super().get_object(queryset)
        
        if self.request.user.is_authenticated:
            self.record_view(obj, self.request.user)
        
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if self.request.user.is_authenticated:
            context['is_favorite'] = self.is_favorite(self.object, self.request.user)
            context['favorite_post_ids'] = [self.object.pk] if context['is_favorite'] else []
        else:
            context['is_favorite'] = False
            context['favorite_post_ids'] = []
        
        context['view_count'] = self.get_view_count(self.object)
        
        context['is_author'] = (
            self.request.user.is_authenticated and 
            self.request.user == self.object.user
        )
        
        return context


class BasePostCreateView(LoginRequiredMixin, CreateView):
    """Базовое представление для создания объявления"""
    template_name = 'post/post_form.html'
    category_slug = None
    success_message = _('Объявление успешно создано и отправлено на модерацию')
    
    def get_form_kwargs(self):
        """Передать дополнительные параметры в форму"""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        if self.category_slug:
            kwargs['category_slug'] = self.category_slug
        return kwargs
    
    def form_valid(self, form):
        """Обработка валидной формы"""
        self.object = form.save(commit=False)
        self.object.user = self.request.user
        
        try:
            self.object.full_clean() 
            self.object.save()
            messages.success(self.request, self.success_message)
            return super().form_valid(form)
        except ValidationError as e:
            form.add_error(None, e)
            return self.form_invalid(form)
    
    def get_success_url(self):
        """URL для перенаправления после успешного создания"""
        return reverse_lazy('core:home')


class BasePostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Базовое представление для редактирования объявления"""
    template_name = 'post/post_form.html'
    
    category_slug = None
    success_message = _('Объявление успешно обновлено и отправлено на модерацию')
    
    def test_func(self):
        """Проверка прав доступа - только автор может редактировать"""
        post = self.get_object()
        return self.request.user == post.user
    
    def get_form_kwargs(self):
        """Передать дополнительные параметры в форму"""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        if self.category_slug:
            kwargs['category_slug'] = self.category_slug
        return kwargs
    
    def form_valid(self, form):
        """Обработка валидной формы"""
        # При обновлении отправляем на модерацию
        form.instance.status = 0  # Не проверено
        messages.success(self.request, self.success_message)
        return super().form_valid(form)
    
    def get_success_url(self):
        """URL для перенаправления после успешного обновления"""
        return reverse_lazy('user:author_profile', kwargs={'author_id': self.request.user.id})


class BasePostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """Базовое представление для мягкого удаления поста"""
    model = AbsPost
    
    def test_func(self):
        """Проверка прав доступа - только автор может удалять"""
        post = self.get_object()
        return self.request.user == post.user
    
    def post(self, request, *args, **kwargs):
        """Обработка POST запроса для удаления"""
        post = self.get_object()
        post.soft_delete()
        messages.success(request, _('Объявление успешно удалено'))
        
        # Возвращаем HTMX ответ или обычное перенаправление
        if request.headers.get('HX-Request'):
            return HttpResponse(
                status=200,
                                headers={'HX-Trigger': f'post-deleted-{post.pk}'}
            )
        
        return redirect('user:author_profile', author_id=request.user.id)


class CategorySpecificMixin:
    """Миксин для работы с категориями постов"""
    
    def get_category_filters(self, category_slug):
        """Получить специфичные фильтры для категории"""
        filters = {}
        
        if category_slug == 'rabota':
            # Фильтры для вакансий
            experience = self.request.GET.get('experience')
            work_format = self.request.GET.get('work_format')
            work_schedule = self.request.GET.get('work_schedule')
            
            if experience and experience.isdigit():
                filters['postjob__experience'] = experience
            if work_format and work_format.isdigit():
                filters['postjob__work_format'] = work_format
            if work_schedule and work_schedule.isdigit():
                filters['postjob__work_schedule'] = work_schedule
                
        elif category_slug == 'uslugi':
            # Фильтры для услуг (пока нет специфичных)
            pass
            
        return filters
    
    def get_category_context(self, category_slug):
        """Получить контекст специфичный для категории"""
        context = {}
        
        if category_slug == 'rabota':
            from ework_job.choices import EXPERIENCE_CHOICES, WORK_FORMAT_CHOICES, WORK_SCHEDULE_CHOICES
            context.update({
                'experience_choices': EXPERIENCE_CHOICES,
                'work_format_choices': WORK_FORMAT_CHOICES,
                'work_schedule_choices': WORK_SCHEDULE_CHOICES,
                'experience': self.request.GET.get('experience', ''),
                'work_format': self.request.GET.get('work_format', ''),
                'work_schedule': self.request.GET.get('work_schedule', ''),
                'is_job_category': True,
            })
        elif category_slug == 'uslugi':
            context.update({
                'is_service_category': True,
            })
            
        return context


class PostSearchMixin:
    """Миксин для поиска постов"""
    
    def get_search_queryset(self, base_queryset=None):
        """Получить queryset для поиска"""
        if base_queryset is None:
            base_queryset = AbsPost.objects.filter(
                status=3,
                is_deleted=False
            )
        
        search_query = self.request.GET.get('q', '').strip()
        rubric_id = self.request.GET.get('rubric_id')
        
        queryset = base_queryset
        
        # Фильтрация по рубрике
        if rubric_id and rubric_id.isdigit():
            try:
                super_rubric = SuperRubric.objects.get(pk=rubric_id)
                sub_rubrics = SubRubric.objects.filter(super_rubric=super_rubric)
                sub_ids = sub_rubrics.values_list('id', flat=True)
                queryset = queryset.filter(sub_rubric_id__in=sub_ids)
            except SuperRubric.DoesNotExist:
                pass
        
        # Поисковый запрос
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) | 
                Q(description__icontains=search_query)
            )
        
        return queryset.select_related(
            'user', 'city', 'currency', 'sub_rubric'
        ).order_by('-created_at')


# Устаревшие классы для обратной совместимости
# TODO: Удалить после обновления всех наследников

class BasePostListView_Legacy(BasePostListView):
    """Устаревший класс - используйте BasePostListView"""
    pass


class BasePostCreateView_Legacy(BasePostCreateView):
    """Устаревший класс - используйте BasePostCreateView"""
    pass


class BasePostUpdateView_Legacy(BasePostUpdateView):
    """Устаревший класс - используйте BasePostUpdateView"""
    pass

