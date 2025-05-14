
from django.views.generic import TemplateView
from django.shortcuts import render

from ework_rubric.models import SuperRubric, SubRubric
from ework_job.models import PostJob
from ework_services.models import PostServices
from itertools import chain


def home(request):

    context = {
        "categories" : SuperRubric.objects.all(),
    }

    if request.headers.get("HX-Request"):
        return render(request, "partials/include_index.html", context)
    return render(request, "index.html", context)


class FavoritesView(TemplateView):
    template_name = 'favorites.html'


def modal_select_post(request):
    return render(request, 'modal_select_post.html')


def post_list(request, rubric_pk):
    rubric = SuperRubric.objects.get(pk=rubric_pk)
    print(rubric)
    subrubrics = rubric.rubric_set.all()
    print(subrubrics)
    posts = rubric.post_set()
    print(posts.count())

    context = {
        "rubric": rubric,
        "subrubrics": subrubrics,
        "posts": posts,
    }

    return render(request, 'post_list.html', context)
    

    
    
