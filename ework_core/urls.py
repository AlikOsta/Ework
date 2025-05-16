
from django.urls import path

from . import views

app_name = 'core'

urlpatterns = [
    path('modal-select-post/', views.modal_select_post, name='modal_select_post'),
    path("favorites/", views.FavoriteListView.as_view(), name='favorites'),
    path('post_list/<int:rubric_pk>/', views.PostListByRubricView.as_view(), name='post_list_by_rubric'),
    path('fav/toggle/<int:post_pk>/', views.favorite_toggle, name='favorite_toggle'),
    path('search/', views.SearchPostsView.as_view(), name='search'),
    path("", views.home, name='home'),
]

