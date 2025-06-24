from django.urls import path
from .views import AuthorProfileView, telegram_login, Index, TelegramAuthView, profile_edit, test_login

app_name = 'user'

urlpatterns = [
    path('author/<int:author_id>/', AuthorProfileView.as_view(), name='author_profile'),
    path('profile/edit/', profile_edit, name='profile_edit'),

    # авторизация
    path('telegram_login/', telegram_login, name='telegram_login'),
    path('index/', Index.as_view(), name='index'),
    path('auth/telegram/', TelegramAuthView.as_view(), name='telegram_auth'),

]