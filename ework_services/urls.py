from django.urls import path
from . import views

app_name = 'services'

urlpatterns = [
    path('', views.ServiceListView.as_view(), name='service_list'),
    path('category/<slug:category_slug>/', views.ServiceListView.as_view(), name='service_by_category'),
    path('<int:pk>/', views.ServiceDetailView.as_view(), name='service_detail'),
    path('create/', views.ServiceCreateView.as_view(), name='service_create'),
    path('<int:pk>/edit/', views.ServiceUpdateView.as_view(), name='service_edit'),
    path('<int:pk>/delete/', views.ServiceDeleteView.as_view(), name='service_delete'),
    path('<int:pk>/favorite/', views.toggle_service_favorite, name='toggle_favorite'),
]
