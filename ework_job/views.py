from django.urls import reverse_lazy
from ework_post.views import (
    BasePostListView, 
    BasePostDetailView, 
    BasePostCreateView, 
    BasePostUpdateView, 
    BasePostDeleteView,
    base_toggle_favorite,
)
from .models import PostJob, FavoriteJob, ProductViewJob
from .forms import JobPostForm

from ework_rubric.models import SubRubric

class JobListView(BasePostListView):
    model = PostJob
    category_model = SubRubric
    template_name = 'jobs/job_list.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Вакансии'
        return context


class JobDetailView(BasePostDetailView):
    model = PostJob
    favorite_model = FavoriteJob
    view_model = ProductViewJob
    template_name = 'jobs/job_detail.html'


class JobCreateView(BasePostCreateView):
    model = PostJob
    form_class = JobPostForm
    template_name = 'jobs/job_form.html'
    success_url = reverse_lazy('jobs:job_list')


class JobUpdateView(BasePostUpdateView):
    model = PostJob
    form_class = JobPostForm
    template_name = 'jobs/job_form.html'


class JobDeleteView(BasePostDeleteView):
    model = PostJob
    template_name = 'jobs/job_confirm_delete.html'
    success_url = reverse_lazy('jobs:job_list')


def toggle_job_favorite(request, pk):
    """Добавление/удаление вакансии из избранного"""
    from .models import FavoriteJob, PostJob
    return base_toggle_favorite(request, pk, FavoriteJob, PostJob)