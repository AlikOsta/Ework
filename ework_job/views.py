
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from .models import PostJob
from .forms import JobPostForm
from ework_post.views import BasePostCreateView
from django.utils.translation import gettext as _




class JobCreateView(BasePostCreateView):
    model = PostJob
    form_class = JobPostForm
    template_name = 'job/post_job_form.html'
    success_url = reverse_lazy('home')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        if self.request.headers.get('HX-Request'):
            return JsonResponse({
                'success': True,
                'message': _('Объявление успешно создано и отправлено на модерацию'),
                'redirect_url': self.get_success_url()
            })
        
        return response
