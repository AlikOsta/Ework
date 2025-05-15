from django.urls import path
from .views import JobPostCreateView

app_name = 'jobs'

urlpatterns = [
    path('create/', JobPostCreateView.as_view(), name='job_create'),
]
