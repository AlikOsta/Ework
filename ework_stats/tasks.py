from django.utils import timezone
from django.db.models import Count
from datetime import timedelta
from .models import DailyStats
from ework_user_tg.models import TelegramUser
from ework_post.models import AbsPost, PostView, Favorite

def collect_daily_stats():
    """Собирает статистику за вчерашний день и сегодня."""
    today = timezone.now().date()
    yesterday = today - timedelta(days=1)
    
    # Собираем статистику за вчера
    yesterday_stats = collect_stats_for_date(yesterday)
    
    # Собираем статистику за сегодня
    today_stats = collect_stats_for_date(today)
    
    return {
        'yesterday': yesterday_stats,
        'today': today_stats
    }

def collect_stats_for_date(date):
    """Собирает статистику за указанную дату."""
    # Считаем новых пользователей за указанную дату
    new_users = TelegramUser.objects.filter(
        date_joined__date=date
    ).count()
    
    # Считаем новые объявления за указанную дату
    new_posts = AbsPost.objects.filter(
        created_at__date=date
    ).count()
    
    # Считаем просмотры за указанную дату
    post_views = PostView.objects.filter(
        created_at__date=date
    ).count()
    
    # Считаем добавления в избранное за указанную дату
    favorites_added = Favorite.objects.filter(
        created_at__date=date
    ).count()
    
    # Сохраняем или обновляем статистику
    stats, created = DailyStats.objects.update_or_create(
        date=date,
        defaults={
            'new_users': new_users,
            'new_posts': new_posts,
            'post_views': post_views,
            'favorites_added': favorites_added,
        }
    )
    
    return {
        'date': date,
        'new_users': new_users,
        'new_posts': new_posts,
        'post_views': post_views,
        'favorites_added': favorites_added,
        'created': created
    }
