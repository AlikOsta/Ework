from django.utils import timezone
from django.db.models import Count
from datetime import timedelta
from .models import DailyStats
from ework_user_tg.models import TelegramUser
from ework_post.models import AbsPost, PostView, Favorite

def collect_daily_stats():
    """Собирает статистику за вчерашний день."""
    yesterday = timezone.now().date() - timedelta(days=1)
    
    # Считаем новых пользователей за вчера
    new_users = TelegramUser.objects.filter(
        date_joined__date=yesterday
    ).count()
    
    # Считаем новые объявления за вчера
    new_posts = AbsPost.objects.filter(
        created_at__date=yesterday
    ).count()
    
    # Считаем просмотры за вчера
    post_views = PostView.objects.filter(
        created_at__date=yesterday
    ).count()
    
    # Считаем добавления в избранное за вчера
    favorites_added = Favorite.objects.filter(
        created_at__date=yesterday
    ).count()
    
    # Сохраняем или обновляем статистику
    stats, created = DailyStats.objects.update_or_create(
        date=yesterday,
        defaults={
            'new_users': new_users,
            'new_posts': new_posts,
            'post_views': post_views,
            'favorites_added': favorites_added,
        }
    )
    
    return {
        'date': yesterday,
        'new_users': new_users,
        'new_posts': new_posts,
        'post_views': post_views,
        'favorites_added': favorites_added,
        'created': created
    }