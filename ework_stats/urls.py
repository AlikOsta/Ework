from django.urls import path
from . import views

app_name = 'ework_stats'

urlpatterns = [
    path('dashboard/', views.dashboard_stats, name='dashboard_stats'),
    path('users/', views.user_stats, name='user_stats'),
    path('posts/', views.post_stats, name='post_stats'),
    path('views/', views.views_stats, name='views_stats'),
    path('finance/', views.finance_stats, name='finance_stats'),
    
    # API endpoints
    path('api/users/', views.api_users_stats, name='api_users_stats'),
    path('api/posts/', views.api_posts_stats, name='api_posts_stats'),
    path('api/views/', views.api_views_stats, name='api_views_stats'),
    path('api/revenue/', views.api_revenue_stats, name='api_revenue_stats'),
    path('api/finance/', views.api_revenue_stats, name='api_finance_stats'),  # Alias
]
