
from django.urls import reverse_lazy
from django.utils.translation import gettext as _

from .models import PostServices
from .forms import ServicesPostForm
from ework_post.views import BasePostCreateView


class ServicesPostCreateView(BasePostCreateView):
    model = PostServices
    form_class = ServicesPostForm
    template_name = 'services/post_services_form.html'

    def get_success_url(self):
        return reverse_lazy('home')
    
    

    

