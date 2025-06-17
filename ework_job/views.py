
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from .models import PostJob
from .forms import JobPostForm
from ework_post.views import BasePostCreateView, BasePostUpdateView


class JobPostCreateView(BasePostCreateView):
    model = PostJob
    form_class = JobPostForm
    template_name = 'job/post_job_form.html'
    
    def get_success_url(self):
        return reverse_lazy('core:home')
    

class JobPostUpdateView(BasePostUpdateView):
    """Редактирование вакансии"""
    model = PostJob
    form_class = JobPostForm
    template_name = 'job/post_job_form.html'
    success_message = _('Вакансия успешно обновлена и отправлена на модерацию')
    
    def get_form_kwargs(self):
        """Переопределяем чтобы не передавать category_slug"""
        kwargs = super(BasePostUpdateView, self).get_form_kwargs()  
        kwargs['user'] = self.request.user
        return kwargs