
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils.translation import gettext as _

from .models import PostJob
from .forms import JobPostForm
from ework_post.views import BasePostCreateView


class JobPostCreateView(BasePostCreateView):
    model = PostJob
    form_class = JobPostForm
    template_name = 'job/post_job_form.html'
    
    def get_success_url(self):
        return reverse_lazy('home')
    

def add_job_post(request):
    if request.method == 'POST':
        form = JobPostForm(request.POST)
        if form.is_valid():
            form.save()
            return render(request, '/')
    else:
        form = JobPostForm()
    return render(request, 'job/add_job_post.html', {'form': form})

