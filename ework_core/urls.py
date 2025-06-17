
from django.urls import path

from . import views

app_name = 'core'

urlpatterns = [
    path('modal-select-post/', views.modal_select_post, name='modal_select_post'),
    path("favorites/", views.FavoriteListView.as_view(), name='favorites'),
    path('post_list/<int:rubric_pk>/', views.PostListByRubricView.as_view(), name='post_list_by_rubric'),
    path('post/<int:post_pk>/favorite/', views.toggle_favorite, name='favorite_toggle'),
    path('product/<int:pk>/', views.PostDetailView.as_view(), name='product_detail'),

    path('banner-ad-info/', views.banner_ad_info, name='banner_ad_info'),
    path('banner/<int:banner_id>/', views.banner_view, name='banner_view'),

    path('premium/', views.premium, name='premium'),

    path('post/<int:pk>/status/<int:status>/', views.change_post_status, name='change_post_status'),
    path('post/<int:pk>/edit/', views.post_edit, name='post_edit'),
    path('post/<int:pk>/delete/', views.post_delete_confirm, name='post_delete_confirm'),

    path("", views.home, name='home'),

]

