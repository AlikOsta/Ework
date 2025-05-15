
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from ework_rubric.models import SuperRubric, SubRubric
from ework_post.models import AbsPost, Favorite
from ework_post.views import BasePostListView

from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django import template


def home(request):
    context = {
        "categories" : SuperRubric.objects.all(),
    }

    if request.headers.get("HX-Request"):
        return render(request, "partials/include_index.html", context)
    return render(request, "index.html", context)
    

def modal_select_post(request):
    return render(request, 'partials/modal_select_post.html')


class PostListView(BasePostListView):
    pass


def post_list_by_rubric(request, rubric_pk):   
    super_rubric = get_object_or_404(SuperRubric, pk=rubric_pk)
    sub_rubrics = SubRubric.objects.filter(super_rubric=super_rubric)

    sub_ids = sub_rubrics.values_list('id', flat=True)

    posts = (AbsPost.objects
            #  .filter(status=3, sub_rubric_id__in=sub_ids)
             .filter(sub_rubric_id__in=sub_ids)
             .order_by('-created_at'))

    favorite_post_ids = []
    if request.user.is_authenticated:
        favorite_post_ids = Favorite.objects.filter(
            user=request.user, 
            post__in=posts
        ).values_list('post_id', flat=True)
    
    context = {
        'categories': sub_rubrics,
        'posts': posts,
        'favorite_post_ids': favorite_post_ids,
    }

    return render(request, 'partials/post_list.html', context)



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
