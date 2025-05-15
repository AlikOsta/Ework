
from django.urls import path

from . import views

app_name = 'core'

urlpatterns = [
    path('modal-select-post/', views.modal_select_post, name='modal_select_post'),
    path("favorites/", views.FavoritesView.as_view(), name='favorites'),
    path('post_list/<int:rubric_pk>/', views.post_list_by_rubric, name='post_list_by_rubric'),
    path("", views.home, name='home'),
]

