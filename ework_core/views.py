
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from ework_rubric.models import SuperRubric, SubRubric
from ework_post.models import AbsPost, Favorite
from ework_post.views import BasePostListView
from django.views.decorators.http import require_POST
from django.db.models import Q

from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, JsonResponse


def home(request):
    context = {
        "categories" : SuperRubric.objects.all(),
    }

    if request.headers.get("HX-Request"):
        return render(request, "partials/include_index.html", context)
    return render(request, "index.html", context)
    

def modal_select_post(request):
    return render(request, 'partials/modal_select_post.html')


class PostListByRubricView(BasePostListView):
    paginate_by = 50

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Получаем параметры фильтрации (общие)
        price_min = self.request.GET.get('price_min')
        price_max = self.request.GET.get('price_max')
        sub_rubric = self.request.GET.get('sub_rubric')
        sort = self.request.GET.get('sort', 'newest')
        
        # Фильтр по цене
        if price_min and price_min.isdigit():
            queryset = queryset.filter(price__gte=int(price_min))
        if price_max and price_max.isdigit():
            queryset = queryset.filter(price__lte=int(price_max))
            
        # Фильтр по подрубрике
        if sub_rubric and sub_rubric.isdigit():
            queryset = queryset.filter(sub_rubric_id=sub_rubric)
            
        # Получаем slug категории для определения специфичных фильтров
        rubric_pk = self.kwargs.get('rubric_pk')
        category_slug = None
        
        if rubric_pk:
            try:
                super_rubric = SuperRubric.objects.get(pk=rubric_pk)
                category_slug = super_rubric.slug
            except SuperRubric.DoesNotExist:
                pass
        
        # Фильтры для категории "Работа"
        if category_slug == 'rabota':
            experience = self.request.GET.get('experience')
            work_format = self.request.GET.get('work_format')
            work_schedule = self.request.GET.get('work_schedule')
            
            # Получаем ID объявлений типа PostJob
            from ework_job.models import PostJob
            job_ids = PostJob.objects.values_list('id', flat=True)
            
            # Фильтруем только объявления типа PostJob
            job_queryset = queryset.filter(id__in=job_ids)
            
            # Применяем дополнительные фильтры
            if experience and experience.isdigit():
                job_queryset = job_queryset.filter(postjob__experience=experience)
            if work_format and work_format.isdigit():
                job_queryset = job_queryset.filter(postjob__work_format=work_format)
            if work_schedule and work_schedule.isdigit():
                job_queryset = job_queryset.filter(postjob__work_schedule=work_schedule)
                
            # Обновляем queryset только объявлениями типа PostJob
            queryset = job_queryset
                
        # Сортировка (общая для всех категорий)
        if sort == 'oldest':
            queryset = queryset.order_by('created_at')
        elif sort == 'price_asc':
            queryset = queryset.order_by('price')
        elif sort == 'price_desc':
            queryset = queryset.order_by('-price')
        else:  # newest (по умолчанию)
            queryset = queryset.order_by('-created_at')
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Добавляем параметры фильтрации в контекст
        context['price_min'] = self.request.GET.get('price_min', '')
        context['price_max'] = self.request.GET.get('price_max', '')
        context['sub_rubric'] = self.request.GET.get('sub_rubric', '')
        context['sort'] = self.request.GET.get('sort', 'newest')
        context['experience'] = self.request.GET.get('experience', '')
        context['work_format'] = self.request.GET.get('work_format', '')
        context['work_schedule'] = self.request.GET.get('work_schedule', '')
        
        # Определяем категорию и добавляем в контекст
        rubric_pk = self.kwargs.get('rubric_pk')
        if rubric_pk:
            try:
                super_rubric = SuperRubric.objects.get(pk=rubric_pk)
                context['category_slug'] = super_rubric.slug
                context['rubric_pk'] = rubric_pk
                
                # Добавляем флаги для определения типа категории в шаблоне
                context['is_job_category'] = super_rubric.slug == 'rabota'
                context['is_service_category'] = super_rubric.slug == 'uslugi'
            except SuperRubric.DoesNotExist:
                pass
        
        # Добавляем избранные посты, если пользователь авторизован
        if self.request.user.is_authenticated:
            favorite_post_ids = Favorite.objects.filter(
                user=self.request.user, 
                post__in=context['posts']
            ).values_list('post_id', flat=True)
            context['favorite_post_ids'] = favorite_post_ids
        
        return context



class FavoriteListView(LoginRequiredMixin, ListView):
    model = Favorite
    template_name = 'favorites.html'
    context_object_name = 'favorites'
    paginate_by = 50

    def get_queryset(self):
        return Favorite.objects.filter(
            user=self.request.user,
            post__status=3 
        ).select_related('post')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Создаем список постов из избранного
        posts = [favorite.post for favorite in context['favorites']]
        context['posts'] = posts
        context['is_favorite'] = True
        
        return context


    

@require_POST
def favorite_toggle(request, post_pk):
    post = get_object_or_404(AbsPost, pk=post_pk)
    
    try:
        favorite = Favorite.objects.get(user=request.user, post=post)
        favorite.delete()
        is_favorite = False
        
        # Проверяем, находимся ли мы на странице избранного
        is_favorites_page = request.headers.get('HX-Current-URL', '').endswith('/favorites/')
        if is_favorites_page:
            return HttpResponse("", headers={"HX-Trigger": f"remove-favorite-{post.pk}"})
        
    except Favorite.DoesNotExist:
        Favorite.objects.create(user=request.user, post=post)
        is_favorite = True

    # Возвращаем обновленную кнопку избранного
    context = {
        'post': post,
        'is_favorite': is_favorite,
        'favorite_post_ids': [post.pk] if is_favorite else []
    }

    return render(request, 'partials/favorite_button.html', context)



class SearchPostsView(BasePostListView):
    """Представление для поиска объявлений"""
    template_name = 'partials/search_results.html'
    
    def get(self, request, *args, **kwargs):
        if not request.GET.get('q'):
            rubric_id = request.GET.get('rubric_id')
            if rubric_id:
                super_rubric = SuperRubric.objects.get(pk=rubric_id)
                sub_rubrics = SubRubric.objects.filter(super_rubric=super_rubric)
                sub_ids = sub_rubrics.values_list('id', flat=True)
                posts = AbsPost.objects.filter(status=3, sub_rubric_id__in=sub_ids).order_by('-created_at')
                
                context = {
                    'categories': sub_rubrics,
                    'posts': posts,
                    'rubric_pk': rubric_id,
                }
                return render(request, 'partials/post_list.html', context)
            else:
                context = {
                    "categories": SuperRubric.objects.all(),
                }
                return render(request, "partials/include_index.html", context)
        
        return super().get(request, *args, **kwargs) 
    
    def get_queryset(self):
        queryset = AbsPost.objects.filter(status=3)
        search_query = self.request.GET.get('q', '')
        rubric_id = self.request.GET.get('rubric_id')
        
        if rubric_id and rubric_id.isdigit():
            try:
                super_rubric = SuperRubric.objects.get(pk=rubric_id)
                sub_rubrics = SubRubric.objects.filter(super_rubric=super_rubric)
                sub_ids = sub_rubrics.values_list('id', flat=True)
                queryset = queryset.filter(sub_rubric_id__in=sub_ids)
            except SuperRubric.DoesNotExist:
                pass
        
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) | 
                Q(description__icontains=search_query)
            )
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        
        rubric_id = self.request.GET.get('rubric_id')
        if rubric_id:
            try:
                super_rubric = SuperRubric.objects.get(pk=rubric_id)
                sub_rubrics = SubRubric.objects.filter(super_rubric=super_rubric)
                context['categories'] = sub_rubrics
                context['active_rubric_id'] = rubric_id
            except SuperRubric.DoesNotExist:
                pass
        
        return context
