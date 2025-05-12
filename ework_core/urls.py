
from django.urls import path

from . import views

app_name = 'core'

urlpatterns = [
    path('modal-select-post/', views.modal_select_post, name='modal_select_post'),
    path("", views.HomeView.as_view(), name='home'),
]

