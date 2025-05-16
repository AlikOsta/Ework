
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from ework_rubric.models import SuperRubric, SubRubric
from ework_post.models import AbsPost, Favorite
from ework_post.views import BasePostListView
from django.db.models import Q

from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse


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
        return super().get_queryset()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context



class FavoriteListView(LoginRequiredMixin, ListView):
    model = Favorite
    template_name = 'favorites.html'
    context_object_name = 'favorites'
    paginate_by = 10

    def get_queryset(self):
        return Favorite.objects.filter(
            user=self.request.user,
            post__status=3 
        ).select_related('post')
    

@login_required
def favorite_toggle(request, post_pk):
    post = get_object_or_404(AbsPost, pk=post_pk)
    
    try:
        favorite = Favorite.objects.get(user=request.user, post=post)
        favorite.delete()
        is_favorite = False
        
        is_favorites_page = request.headers.get('HX-Current-URL', '').endswith('/favorites/')
        if is_favorites_page:
            return HttpResponse("", headers={"HX-Trigger": f"remove-favorite-{post.pk}"})
        
    except Favorite.DoesNotExist:
        Favorite.objects.create(user=request.user, post=post)
        is_favorite = True

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
                }
                return render(request, 'partials/post_list.html', context)
            else:
                context = {
                    "categories": SuperRubric.objects.all(),
                }
                return render(request, "partials/include_index.html", context)
        
        # Этот return должен быть на том же уровне отступа, что и if
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
