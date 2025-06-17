from django.urls import path
from .views import ServicesPostCreateView, ServicesPostUpdateView

app_name = 'services'

urlpatterns = [
    path('create/', ServicesPostCreateView.as_view(), name='services_create'),
    path('edit/<int:pk>/', ServicesPostUpdateView.as_view(), name='post_edit'),
]
