
from django.urls import path

from . import views
from ework_post.views import PricingCalculatorView, PostPaymentSuccessView

app_name = 'core'

urlpatterns = [
    path('modal-select-post/', views.modal_select_post, name='modal_select_post'),
    path("favorites/", views.FavoriteListView.as_view(), name='favorites'),
    path('post_list/<int:rubric_pk>/', views.PostListByRubricView.as_view(), name='post_list_by_rubric'),
    path('api/post_list/<int:rubric_pk>/', views.PostListByRubricHTMXView.as_view(), name='post_list_by_rubric_htmx'),
    path('post/<int:post_pk>/favorite/', views.toggle_favorite, name='favorite_toggle'),
    path('product/<int:pk>/', views.PostDetailView.as_view(), name='product_detail'),

    path('banner-ad-info/', views.banner_ad_info, name='banner_ad_info'),
    path('banner/<int:banner_id>/', views.banner_view, name='banner_view'),

    path('premium/', views.premium, name='premium'),

    path('post/<int:pk>/status/<int:status>/', views.change_post_status, name='change_post_status'),
    path('post/<int:pk>/edit/', views.post_edit, name='post_edit'),
    path('post/<int:pk>/delete/', views.post_delete_confirm, name='post_delete_confirm'),

    # API для динамического расчета стоимости
    path('api/pricing-calculator/', PricingCalculatorView.as_view(), name='pricing_calculator'),
    
    # Публикация после оплаты
    path('api/post-payment-success/<int:payment_id>/', PostPaymentSuccessView.as_view(), name='post_payment_success'),
    
    # API для создания инвойса
    path('api/create-invoice/', views.CreateInvoiceView.as_view(), name='create_invoice'),

    path("", views.home, name='home'),

]

