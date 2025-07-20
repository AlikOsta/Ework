from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Sum, F, Q, Avg
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth, TruncYear
from django.utils import timezone
from ework_post.models import AbsPost, PostView, Favorite
from ework_user_tg.models import TelegramUser
from ework_premium.models import Payment
from .tasks import collect_daily_stats
from .models import DailyStats
import datetime


@staff_member_required
def dashboard_stats(request):
    """Отображает общую панель статистики."""
    # Собираем статистику перед отображением страницы
    collect_stats_if_needed()
    
    # Подготовка данных для шаблона
    context = {
        'period_choices': [
            {'value': 'day', 'label': 'День'},
            {'value': 'week', 'label': 'Неделя'},
            {'value': 'month', 'label': 'Месяц'},
            {'value': 'year', 'label': 'Год'}
        ],
        'metrics': [
            {'icon': 'groups', 'id': 'total-users', 'label': 'Всего пользователей'},
            {'icon': 'description', 'id': 'total-posts', 'label': 'Всего объявлений'},
            {'icon': 'task_alt', 'id': 'active-posts', 'label': 'Активных объявлений'},
            {'icon': 'favorite', 'id': 'total-favorites', 'label': 'Добавлено в избранное'},
            {'icon': 'paid', 'id': 'total-revenue', 'label': 'Общий доход (₴)'}
        ],
        'sections': [
            {
                'section': 'users',
                'title': 'Пользователи',
                'chart_id': 'usersChart',
                'metrics': [
                    {'id': 'new-users', 'label': 'Новых пользователей'},
                    {'id': 'active-users', 'label': 'Активных пользователей'},
                    {'id': 'users-growth', 'label': 'Активных за неделю'}
                ]
            },
            {
                'section': 'posts',
                'title': 'Объявления',
                'chart_id': 'postsChart',
                'metrics': [
                    {'id': 'new-posts', 'label': 'Новых объявлений'},
                    {'id': 'posts-moderation', 'label': 'На модерации'},
                    {'id': 'posts-growth', 'label': 'Активных объявлений'}
                ]
            },
            {
                'section': 'finance',
                'title': 'Финансы',
                'chart_id': 'financeChart',
                'metrics': [
                    {'id': 'period-revenue', 'label': 'Доход за период'},
                    {'id': 'total-payments', 'label': 'Всего платежей'},
                    {'id': 'avg-payment', 'label': 'Средний чек'}
                ]
            }
        ]
    }
    
    return render(request, 'admin_stats/dashboard_stats.html', context)



@staff_member_required
def user_stats(request):
    """Отображает статистику пользователей."""
    return render(request, 'admin_stats/user_stats.html')

@staff_member_required
def post_stats(request):
    """Отображает статистику объявлений."""
    return render(request, 'admin_stats/post_stats.html')

@staff_member_required
def views_stats(request):
    """Отображает статистику просмотров и избранного."""
    return render(request, 'admin_stats/views_stats.html')

@staff_member_required
def finance_stats(request):
    """Отображает финансовую статистику."""
    return render(request, 'admin_stats/finance_stats.html')

def collect_stats_if_needed():
    """Проверяет, нужно ли собирать статистику, и собирает её при необходимости."""
    today = timezone.now().date()
    yesterday = today - datetime.timedelta(days=1)
    
    # Проверяем, есть ли статистика за вчерашний день
    if not DailyStats.objects.filter(date=yesterday).exists():
        # Если нет, собираем статистику
        collect_daily_stats()
    
    # Также можно проверить наличие статистики за предыдущие дни
    # и собрать её, если она отсутствует
    for days_ago in range(2, 31):  # Проверяем последние 30 дней
        check_date = today - datetime.timedelta(days=days_ago)
        if not DailyStats.objects.filter(date=check_date).exists():
            # Собираем статистику за этот день
            collect_stats_for_date(check_date)

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
    
    # Сохраняем статистику
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

@staff_member_required
def api_users_stats(request):
    """API для получения статистики пользователей."""
    period = request.GET.get('period', 'month')
    
    # Получаем общее количество пользователей
    total_users = TelegramUser.objects.count()
    
    # Получаем количество активных пользователей (активность за последние 30 дней)
    # Используем created_at вместо last_login, так как last_login может не быть
    active_users = TelegramUser.objects.filter(
        created_at__gte=timezone.now() - datetime.timedelta(days=30)
    ).count()
    
    # Определяем функцию усечения даты в зависимости от периода
    if period == 'day':
        trunc_func = TruncDay
        days_ago = 1
        date_format = '%H:%M'
    elif period == 'week':
        trunc_func = TruncDay
        days_ago = 7
        date_format = '%d.%m'
    elif period == 'year':
        trunc_func = TruncMonth
        days_ago = 365
        date_format = '%b %Y'
    else:  # month
        trunc_func = TruncDay
        days_ago = 30
        date_format = '%d.%m'
    
    # Получаем статистику регистраций за выбранный период
    start_date = timezone.now() - datetime.timedelta(days=days_ago)
    
    registrations = TelegramUser.objects.filter(
        created_at__gte=start_date
    ).annotate(
        date=trunc_func('created_at')
    ).values('date').annotate(
        count=Count('id')
    ).order_by('date')
    
    # Формируем данные для графика
    dates = []
    counts = []
    
    current = start_date
    end_date = timezone.now()
    
    # Создаем словарь с данными регистраций
    reg_dict = {reg['date'].date(): reg['count'] for reg in registrations}
    
    # Заполняем данные для всех дат в периоде
    while current <= end_date:
        if period == 'day':
            date_key = current.replace(minute=0).time()
            date_str = current.strftime(date_format)
            current += datetime.timedelta(hours=1)
        elif period == 'year':
            date_key = current.replace(day=1).date()
            date_str = current.strftime(date_format)
            # Переходим к следующему месяцу
            if current.month == 12:
                current = current.replace(year=current.year + 1, month=1)
            else:
                current = current.replace(month=current.month + 1)
        else:
            date_key = current.date()
            date_str = current.strftime(date_format)
            current += datetime.timedelta(days=1)
        
        dates.append(date_str)
        counts.append(reg_dict.get(date_key, 0) if isinstance(date_key, datetime.date) else 0)
    
    # Вычисляем активность пользователей
    daily_active_users = TelegramUser.objects.filter(
        created_at__gte=timezone.now() - datetime.timedelta(days=1)
    ).count()
    
    weekly_active_users = TelegramUser.objects.filter(
        created_at__gte=timezone.now() - datetime.timedelta(days=7)
    ).count()
    
    monthly_active_users = active_users
    
    # Формируем данные для ответа
    response_data = {
        'total_users': total_users,
        'active_users': active_users,
        'labels': dates,
        'datasets': [
            {
                'label': 'Новые пользователи',
                'data': counts,
                'borderColor': 'rgba(54, 162, 235, 1)',
                'backgroundColor': 'rgba(54, 162, 235, 0.2)'
            }
        ],
        'daily_active_users': daily_active_users,
        'weekly_active_users': weekly_active_users,
        'monthly_active_users': monthly_active_users
    }
    
    return JsonResponse(response_data)

@staff_member_required
def api_posts_stats(request):
    """API для получения статистики объявлений."""
    period = request.GET.get('period', 'month')
    
    # Получаем общее количество объявлений
    total_posts = AbsPost.objects.count()
    
    # Получаем количество активных объявлений (статус = 3 - опубликовано)
    active_posts = AbsPost.objects.filter(status=3).count()
    
    # Определяем функцию усечения даты в зависимости от периода
    if period == 'day':
        trunc_func = TruncDay
        days_ago = 1
        date_format = '%H:%M'
    elif period == 'week':
        trunc_func = TruncDay
        days_ago = 7
        date_format = '%d.%m'
    elif period == 'year':
        trunc_func = TruncMonth
        days_ago = 365
        date_format = '%b %Y'
    else:  # month
        trunc_func = TruncDay
        days_ago = 30
        date_format = '%d.%m'
    
    # Получаем статистику создания объявлений за выбранный период
    start_date = timezone.now() - datetime.timedelta(days=days_ago)
    
    post_creations = AbsPost.objects.filter(
        created_at__gte=start_date
    ).annotate(
        date=trunc_func('created_at')
    ).values('date').annotate(
        count=Count('id')
    ).order_by('date')
    
    # Формируем данные для графика
    dates = []
    counts = []
    
    current = start_date
    end_date = timezone.now()
    
    # Создаем словарь с данными создания объявлений
    post_dict = {post['date'].date(): post['count'] for post in post_creations}
    
    # Заполняем данные для всех дат в периоде
    while current <= end_date:
        if period == 'day':
            date_key = current.replace(minute=0).time()
            date_str = current.strftime(date_format)
            current += datetime.timedelta(hours=1)
        elif period == 'year':
            date_key = current.replace(day=1).date()
            date_str = current.strftime(date_format)
            # Переходим к следующему месяцу
            if current.month == 12:
                current = current.replace(year=current.year + 1, month=1)
            else:
                current = current.replace(month=current.month + 1)
        else:
            date_key = current.date()
            date_str = current.strftime(date_format)
            current += datetime.timedelta(days=1)
        
        dates.append(date_str)
        counts.append(post_dict.get(date_key, 0) if isinstance(date_key, datetime.date) else 0)
    
    # Получаем статистику по статусам объявлений
    status_counts = AbsPost.objects.values('status').annotate(count=Count('id'))
    status_data = [0, 0, 0, 0, 0]  # Инициализируем нулями для всех статусов
    
    for status in status_counts:
        if 0 <= status['status'] <= 4:
            status_data[status['status']] = status['count']
    
    # Получаем статистику по категориям
    from ework_rubric.models import SubRubric
    categories = SubRubric.objects.annotate(post_count=Count('ework_post_abspost_posts')).order_by('-post_count')[:6]
    category_labels = [cat.name for cat in categories]
    category_data = [cat.post_count for cat in categories]
    
    # Если категорий меньше 6, добавляем "Другое"
    if len(category_labels) < 6:
        other_count = total_posts - sum(category_data)
        if other_count > 0:
            category_labels.append('Другое')
            category_data.append(other_count)
    
    # Формируем данные для ответа
    response_data = {
        'total_posts': total_posts,
        'active_posts': active_posts,
        'labels': dates,
        'datasets': [
            {
                'label': 'Новые объявления',
                'data': counts,
                'borderColor': 'rgba(255, 99, 132, 1)',
                'backgroundColor': 'rgba(255, 99, 132, 0.2)'
            }
        ],
        'status_labels': ['На модерации', 'Одобрено', 'Отклонено', 'Опубликовано', 'Архив'],
        'status_data': status_data,
        'category_labels': category_labels,
        'category_data': category_data
    }
    
    return JsonResponse(response_data)

@staff_member_required
def api_views_stats(request):
    """API для получения статистики просмотров и избранного."""
    period = request.GET.get('period', 'month')
    
    # Получаем общее количество просмотров и избранного
    total_views = PostView.objects.count()
    total_favorites = Favorite.objects.count()
    total_posts = AbsPost.objects.count()
    
    # Определяем функцию усечения даты в зависимости от периода
    if period == 'day':
        trunc_func = TruncDay
        days_ago = 1
        date_format = '%H:%M'
    elif period == 'week':
        trunc_func = TruncDay
        days_ago = 7
        date_format = '%d.%m'
    elif period == 'year':
        trunc_func = TruncMonth
        days_ago = 365
        date_format = '%b %Y'
    else:  # month
        trunc_func = TruncDay
        days_ago = 30
        date_format = '%d.%m'
    
    # Получаем статистику просмотров за выбранный период
    start_date = timezone.now() - datetime.timedelta(days=days_ago)
    
    views_stats = PostView.objects.filter(
        created_at__gte=start_date
    ).annotate(
        date=trunc_func('created_at')
    ).values('date').annotate(
        count=Count('id')
    ).order_by('date')
    
    # Получаем статистику избранного за выбранный период
    favorites_stats = Favorite.objects.filter(
        created_at__gte=start_date
    ).annotate(
        date=trunc_func('created_at')
    ).values('date').annotate(
        count=Count('id')
    ).order_by('date')
    
    # Формируем данные для графика
    dates = []
    views_counts = []
    favorites_counts = []
    
    current = start_date
    end_date = timezone.now()
    
    # Создаем словари с данными просмотров и избранного
    views_dict = {view['date'].date(): view['count'] for view in views_stats}
    favorites_dict = {fav['date'].date(): fav['count'] for fav in favorites_stats}
    
    # Заполняем данные для всех дат в периоде
    while current <= end_date:
        if period == 'day':
            date_key = current.replace(minute=0).time()
            date_str = current.strftime(date_format)
            current += datetime.timedelta(hours=1)
        elif period == 'year':
            date_key = current.replace(day=1).date()
            date_str = current.strftime(date_format)
            # Переходим к следующему месяцу
            if current.month == 12:
                current = current.replace(year=current.year + 1, month=1)
            else:
                current = current.replace(month=current.month + 1)
        else:
            date_key = current.date()
            date_str = current.strftime(date_format)
            current += datetime.timedelta(days=1)
        
        dates.append(date_str)
        views_counts.append(views_dict.get(date_key, 0) if isinstance(date_key, datetime.date) else 0)
        favorites_counts.append(favorites_dict.get(date_key, 0) if isinstance(date_key, datetime.date) else 0)
    
    # Получаем топ просматриваемых объявлений
    from django.contrib.contenttypes.models import ContentType
    abs_post_ct = ContentType.objects.get_for_model(AbsPost)
    
    # Подсчитываем просмотры для каждого поста
    post_views_counts = PostView.objects.filter(
        content_type=abs_post_ct
    ).values('object_id').annotate(
        views_count=Count('id')
    ).order_by('-views_count')[:10]
    
    top_posts_data = []
    for item in post_views_counts:
        try:
            post = AbsPost.objects.get(id=item['object_id'])
            top_posts_data.append({
                'title': post.title[:50] + '...' if len(post.title) > 50 else post.title,
                'views': item['views_count'],
                'favorites': Favorite.objects.filter(post=post).count()
            })
        except AbsPost.DoesNotExist:
            continue
    
    # Средние показатели
    avg_views_per_post = total_views / total_posts if total_posts > 0 else 0
    avg_favorites_per_post = total_favorites / total_posts if total_posts > 0 else 0
    
    # Формируем данные для ответа
    response_data = {
        'total_views': total_views,
        'total_favorites': total_favorites,
        'avg_views_per_post': round(avg_views_per_post, 2),
        'avg_favorites_per_post': round(avg_favorites_per_post, 2),
        'labels': dates,
        'datasets': [
            {
                'label': 'Просмотры',
                'data': views_counts,
                'borderColor': 'rgba(75, 192, 192, 1)',
                'backgroundColor': 'rgba(75, 192, 192, 0.2)'
            },
            {
                'label': 'Избранное',
                'data': favorites_counts,
                'borderColor': 'rgba(255, 206, 86, 1)',
                'backgroundColor': 'rgba(255, 206, 86, 0.2)'
            }
        ],
        'top_posts': top_posts_data
    }
    
    return JsonResponse(response_data)

@staff_member_required
def api_revenue_stats(request):
    """API для получения статистики доходов."""
    period = request.GET.get('period', 'month')
    
    # Получаем общий доход
    total_revenue = Payment.objects.filter(status='paid').aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    # Получаем количество платежей
    total_payments = Payment.objects.filter(status='paid').count()
    
    # Определяем функцию усечения даты в зависимости от периода
    if period == 'day':
        trunc_func = TruncDay
        days_ago = 1
        date_format = '%H:%M'
    elif period == 'week':
        trunc_func = TruncDay
        days_ago = 7
        date_format = '%d.%m'
    elif period == 'year':
        trunc_func = TruncMonth
        days_ago = 365
        date_format = '%b %Y'
    else:  # month
        trunc_func = TruncDay
        days_ago = 30
        date_format = '%d.%m'
    
    # Получаем статистику доходов за выбранный период
    start_date = timezone.now() - datetime.timedelta(days=days_ago)
    
    revenue_stats = Payment.objects.filter(
        status='paid',
        paid_at__gte=start_date
    ).annotate(
        date=trunc_func('paid_at')
    ).values('date').annotate(
        total=Sum('amount')
    ).order_by('date')
    
    # Формируем данные для графика
    dates = []
    revenue_counts = []
    
    current = start_date
    end_date = timezone.now()
    
    # Создаем словарь с данными доходов
    revenue_dict = {rev['date'].date(): float(rev['total']) for rev in revenue_stats}
    
    # Заполняем данные для всех дат в периоде
    while current <= end_date:
        if period == 'day':
            date_key = current.replace(minute=0).time()
            date_str = current.strftime(date_format)
            current += datetime.timedelta(hours=1)
        elif period == 'year':
            date_key = current.replace(day=1).date()
            date_str = current.strftime(date_format)
            # Переходим к следующему месяцу
            if current.month == 12:
                current = current.replace(year=current.year + 1, month=1)
            else:
                current = current.replace(month=current.month + 1)
        else:
            date_key = current.date()
            date_str = current.strftime(date_format)
            current += datetime.timedelta(days=1)
        
        dates.append(date_str)
        revenue_counts.append(revenue_dict.get(date_key, 0) if isinstance(date_key, datetime.date) else 0)
    
    # Средний чек
    avg_payment = total_revenue / total_payments if total_payments > 0 else 0
    
    # Формируем данные для ответа
    response_data = {
        'total_revenue': float(total_revenue),
        'total_payments': total_payments,
        'avg_payment': round(float(avg_payment), 2),
        'labels': dates,
        'datasets': [
            {
                'label': 'Доход',
                'data': revenue_counts,
                'borderColor': 'rgba(153, 102, 255, 1)',
                'backgroundColor': 'rgba(153, 102, 255, 0.2)'
            }
        ]
    }
    
    return JsonResponse(response_data)

