
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.utils.translation import gettext as _

from .models import PostJob
from .forms import JobPostForm
from ework_post.views import BasePostCreateView
from django.shortcuts import render, redirect
from ework_user_tg.models import TelegramUser


class JobPostCreateView(BasePostCreateView):
    model = PostJob
    form_class = JobPostForm
    template_name = 'job/post_job_form.html'
    success_url = reverse_lazy('home')


def add_job(response):
    if response.method == 'POST':
        form = JobPostForm(response.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.user = response.user
            job.save()
            return redirect("home")
    else:
        form = JobPostForm()
    return render(response, 'job/post_job_form.html', {'form': form})
