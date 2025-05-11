
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
    
        



