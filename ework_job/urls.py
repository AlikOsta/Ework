from django.urls import path
from . import views

app_name = 'jobs'

urlpatterns = [
    path('create/', views.JobCreateView.as_view(), name='job_create'),

]
