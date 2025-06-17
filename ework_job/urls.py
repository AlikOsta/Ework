from django.urls import path
from .views import JobPostCreateView, JobPostUpdateView

app_name = 'jobs'

urlpatterns = [
    path('create/', JobPostCreateView.as_view(), name='job_create'),
    path('edit/<int:pk>/', JobPostUpdateView.as_view(), name='post_edit'),
]
