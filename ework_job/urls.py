from django.urls import path
from .views import JobPostCreateView, job_post_list, job_post_detail

app_name = 'jobs'

urlpatterns = [
    path('', job_post_list, name='job_list'),
    path('create/', JobPostCreateView.as_view(), name='job_create'),
]
