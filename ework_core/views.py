
from django.views.generic import TemplateView
from django.shortcuts import render

class HomeView(TemplateView):
    template_name = 'index.html'


def modal_select_post(request):
    return render(request, 'modal_select_post.html')