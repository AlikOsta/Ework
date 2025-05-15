
from django.views.generic import TemplateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render

from ework_rubric.models import SuperRubric, SubRubric
from ework_job.models import PostJob
from ework_services.models import PostServices

from ework_post.models  import Favorite

from itertools import chain
from operator import attrgetter
from django.shortcuts import get_object_or_404, render


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


def post_list(request, rubric_pk):
    superrubric = get_object_or_404(SuperRubric, pk=rubric_pk)
    sub_rubrics = SubRubric.objects.filter(super_rubric=superrubric)

    jobs = PostJob.objects.filter(status = 3, sub_rubric__in=sub_rubrics)
    services = PostServices.objects.filter(status = 3, sub_rubric__in=sub_rubrics)

    products = sorted(chain(jobs, services), key=attrgetter('created_at'),
        reverse=True
    )

    context = {
        'products': products,
        'categories': sub_rubrics,
        'superrubric': superrubric,
    }

    return render(request, 'partials/post_list.html', context)


from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.contrib.contenttypes.models import ContentType
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required


@login_required
@require_POST
def toggle_favorite(request):
    print("---------------------------------------++++++-------------------------------------------------")
    ct_label = request.POST.get('ct', '')
    obj_id  = request.POST.get('obj_id', '')

    try:
        app_label, model = ct_label.split('.')
        ct = ContentType.objects.get(app_label=app_label, model=model.lower())
        model_cls = ct.model_class()
        obj = get_object_or_404(model_cls, pk=obj_id)
    except Exception:
        return render(request, 'partials/favorite_button.html', {
            'product': None,
            'is_favorite': False,
            'fav_count': 0,
        }, status=400)

    fav, created = Favorite.objects.get_or_create(
        user=request.user,
        content_type=ct,
        object_id=obj.pk
    )
    if not created:
        fav.delete()
        print("Удалил")
        is_fav = False
    else:
        print("Добавил")
        is_fav = True

    fav_count = Favorite.objects.filter(
        content_type=ct,
        object_id=obj.pk
    ).count()

    return render(request, 'partials/favorite_button.html', {
        'product': obj,
        'is_favorite': is_fav,
        'fav_count': fav_count,
    })
    

    
    
