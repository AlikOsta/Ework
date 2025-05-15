
from django.urls import path

from . import views

app_name = 'core'

urlpatterns = [
    path('modal-select-post/', views.modal_select_post, name='modal_select_post'),
    path("favorites/", views.FavoritesView.as_view(), name='favorites'),
    path("post-list/<int:rubric_pk>/", views.post_list, name='post_list'),
    path('favorite/toggle/', views.toggle_favorite, name='toggle_favorite'),
    path("", views.home, name='home'),
]

