from django.urls import path
from .views import ServicesPostCreateView

app_name = 'services'

urlpatterns = [
    path('create/', ServicesPostCreateView.as_view(), name='services_create'),
]
