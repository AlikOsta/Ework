
from django.views.generic import TemplateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render

from ework_rubric.models import SuperRubric, SubRubric
from ework_job.models import PostJob
from ework_services.models import PostServices

from ework_post.models  import Favorite

from itertools import chain
from operator import attrgetter
from django.shortcuts import get_object_or_404

from ework_post.models import AbsPost



def home(request):
    context = {
        "categories" : SuperRubric.objects.all(),
    }

    if request.headers.get("HX-Request"):
        return render(request, "partials/include_index.html", context)
    return render(request, "index.html", context)


class FavoritesView(LoginRequiredMixin, ListView):
    model = Favorite
    template_name = 'favorites.html'
    context_object_name = 'favorites'

    def get_queryset(self):
        return Favorite.objects.filter(
            user=self.request.user
        ).select_related('content_type').order_by('-created_at')
    

def modal_select_post(request):
    return render(request, 'partials/modal_select_post.html')


def post_list_by_rubric(request, rubric_pk):   
    super_rubric = get_object_or_404(SuperRubric, pk=rubric_pk)
    sub_rubrics = SubRubric.objects.filter(super_rubric=super_rubric)

    sub_ids = sub_rubrics.values_list('id', flat=True)

    posts = (AbsPost.objects
             .filter(status=3, sub_rubric_id__in=sub_ids)
             .order_by('-created_at'))
    
    context = {
        'categories': sub_rubrics,
        'products': posts,
    }

    return render(request, 'partials/post_list.html', context)
 
