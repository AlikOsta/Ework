from django.views.generic import TemplateView, ListView
from django.db.models import Count, Q
from django.shortcuts import render
from ework_rubric.models import SuperRubric, SubRubric
from ework_job.models import PostJob
from ework_services.models import PostServices


class ProductListView(TemplateView):
    template_name = 'index.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        return context


class JobsListView(ListView):
    model = PostJob
    template_name = 'partials/jobs.html'
    paginate_by = 50
    context_object_name = 'latest_jobs'

    def get_queryset(self):        
        qs = PostJob.objects.all().filter(status=3)
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q))
            
        rubric = self.request.GET.get('rubric')
        if rubric:
            qs = qs.filter(rubric__slug=rubric)
            
        return qs.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class ServicesListView(ListView):
    model = PostServices 
    template_name = 'partials/services.html'
    paginate_by = 50
    context_object_name = 'latest_services'

    def get_queryset(self):
        qs = PostServices.objects.all().filter(status=3)
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q))
        rubric = self.request.GET.get('rubric')
        if rubric:
            qs = qs.filter(rubric__slug=rubric)
        return qs.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
