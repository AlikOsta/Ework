from urllib.parse import parse_qsl, unquote
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import TemplateView, ListView
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.urls import reverse
import logging
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth import login
from django.utils import timezone
from django.conf import settings
from .verify_telegram_init_data import verify_init_data
import json
from ework_post.models import AbsPost, Favorite
from .forms import UserProfileForm, UserRatingForm
from django.views.decorators.csrf import csrf_exempt
from django.utils import translation
from django.db.models import Count, Avg
from django.contrib.contenttypes.models import ContentType

logger = logging.getLogger(__name__)
User = get_user_model()


@method_decorator(login_required(login_url='users:telegram_auth'), name='dispatch')
class AuthorProfileView(ListView):
    """Оптимизированное представление профиля автора"""
    model = AbsPost
    template_name = 'user_ework/author_profile.html'
    context_object_name = 'posts'
    paginate_by = 20
    
    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self._author = None
        self._is_own_profile = None

    def get_author(self):
        """Получить автора с кэшированием"""
        if self._author is None:
            self._author = get_object_or_404(User, id=self.kwargs['author_id'])
        return self._author
    
    def get_template_names(self):
        if self.request.headers.get('HX-Request') == 'true':
            return ['user_ework/author_profile.html']
        else:
            return ['user_ework/author_profile_full.html']
    
    def is_own_profile(self):
        """Проверить, является ли профиль собственным"""
        if self._is_own_profile is None:
            try:
                self._is_own_profile = (
                    self.request.user.is_authenticated and 
                    self.request.user.id == self.get_author().id
                )
            except Exception as e:
                logger.error(f"Error checking if own profile: {e}")
                self._is_own_profile = False
        return self._is_own_profile

    def get_posts_by_status(self):
        """Получить посты автора, сгруппированные по статусам с оптимизацией"""
        author = self.get_author()
        is_own = self.is_own_profile()
        
        # Базовый queryset с оптимизацией
        base_queryset = AbsPost.objects.filter(
            user=author,
            is_deleted=False
        ).select_related(
            'user', 'city', 'currency', 'sub_rubric', 'sub_rubric__super_rubric'
        ).prefetch_related('favorited_by').order_by('-created_at')
        
        if is_own:
            # Для собственного профиля получаем посты всех статусов одним запросом
            posts = list(base_queryset)
            posts_by_status = {
                'published': [p for p in posts if p.status == 3],
                'pending': [p for p in posts if p.status == 0],
                'approved': [p for p in posts if p.status == 1],
                'rejected': [p for p in posts if p.status == 2],
                'archived': [p for p in posts if p.status == 4],
            }
        else:
            # Для чужого профиля показываем только опубликованные
            published_posts = list(base_queryset.filter(status=3))
            posts_by_status = {
                'published': published_posts,
                'pending': [],
                'approved': [],
                'rejected': [],
                'archived': [],
            }
        
        return posts_by_status

    def get_queryset(self):
        """Получить объявления для основного списка (опубликованные)"""
        posts_by_status = self.get_posts_by_status()
        return posts_by_status['published']
    
    def get_context_data(self, **kwargs):
        try:
            context = super().get_context_data(**kwargs)
            author = self.get_author()
            is_own_profile = self.is_own_profile()
            posts_by_status = self.get_posts_by_status()
            
            # Основные данные профиля
            context.update({
                'author': author,
                'is_own_profile': is_own_profile,
            })
            
            # Посты по статусам
            context.update({
                'published_products': posts_by_status['published'],
                'pending_products': posts_by_status['pending'],
                'approved_products': posts_by_status['approved'],
                'rejected_products': posts_by_status['rejected'],
                'archived_products': posts_by_status['archived'],
            })
            
            # Счетчики для бейджей
            context.update({
                'published_count': len(posts_by_status['published']),
                'pending_count': len(posts_by_status['pending']) + len(posts_by_status['approved']),
                'rejected_count': len(posts_by_status['rejected']),
                'archived_count': len(posts_by_status['archived']),
                'total_posts_count': sum(len(posts) for posts in posts_by_status.values()),
            })
            
            # Избранные посты для текущего пользователя
            if self.request.user.is_authenticated:
                all_posts = []
                for posts_list in posts_by_status.values():
                    all_posts.extend(posts_list)
                
                if all_posts:
                    favorite_post_ids = Favorite.objects.filter(
                        user=self.request.user,
                        post__in=all_posts
                    ).values_list('post_id', flat=True)
                    context['favorite_post_ids'] = list(favorite_post_ids)
                else:
                    context['favorite_post_ids'] = []
            else:
                context['favorite_post_ids'] = []
            
            # Дополнительная статистика для собственного профиля
            if is_own_profile:
                context['profile_stats'] = self.get_profile_stats(author, posts_by_status)
            
            return context
            
        except Exception as e:
            logger.error(f"Error in get_context_data: {e}")
            return {
                'author': self.get_author(), 
                'is_own_profile': False,
                'published_products': [],
                'pending_products': [],
                'approved_products': [],
                'rejected_products': [],
                'archived_products': [],
                'published_count': 0,
                'pending_count': 0,
                'rejected_count': 0,
                'archived_count': 0,
                'total_posts_count': 0,
                'favorite_post_ids': [],
                'profile_stats': {},
            }
    
    def get_profile_stats(self, author, posts_by_status):
        """Получить статистику профиля с оптимизацией"""
        try:
            from ework_post.models import PostView
            
            # Все посты пользователя
            all_posts = []
            for posts_list in posts_by_status.values():
                all_posts.extend(posts_list)
            
            stats = {
                'total_posts': len(all_posts),
                'total_views': 0,
                'total_favorites': 0,
                'avg_price': 0,
            }
            
            if all_posts:
                # Подсчет просмотров одним запросом
                post_ids = [post.pk for post in all_posts]
                content_types = ContentType.objects.get_for_models(
                    *[type(post) for post in all_posts]
                ).values()
                
                total_views = PostView.objects.filter(
                    content_type__in=content_types,
                    object_id__in=post_ids
                ).count()
                
                # Подсчет избранных одним запросом
                total_favorites = Favorite.objects.filter(post__in=all_posts).count()
                
                # Средняя цена только для опубликованных
                published_posts = posts_by_status['published']
                if published_posts:
                    prices = [post.price for post in published_posts if post.price]
                    avg_price = sum(prices) / len(prices) if prices else 0
                else:
                    avg_price = 0
                
                stats.update({
                    'total_views': total_views,
                    'total_favorites': total_favorites,
                    'avg_price': round(avg_price, 2),
                })
            
            return stats
            
        except Exception as e:
            logger.error(f"Error calculating profile stats: {e}")
            return {
                'total_posts': 0,
                'total_views': 0,
                'total_favorites': 0,
                'avg_price': 0,
            }


@login_required
def profile_edit(request):
    """Редактирование профиля"""
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            user = form.save()
            
            # Обрабатываем смену языка
            new_language = form.cleaned_data.get('language')
            if new_language and new_language != request.LANGUAGE_CODE:
                # ИСПРАВЛЕНИЕ: используем строку напрямую
                request.session['django_language'] = new_language
                translation.activate(new_language)
            
            if request.headers.get('HX-Request'):
                return HttpResponse(
                    status=200,
                    headers={
                        'HX-Trigger': 'closeModal',
                        'HX-Redirect': reverse('users:author_profile', kwargs={'author_id': request.user.id})
                    }
                )
            return redirect('users:author_profile', author_id=request.user.id)
    else:
        form = UserProfileForm(instance=request.user)
    
    return render(request, 'user_ework/profile_edit.html', {'form': form})



class Index(TemplateView):
    template_name = 'user_ework/index.html'


class TelegramAuthView(TemplateView):
    template_name = 'user_ework/telegram_auth.html'


@require_POST
@csrf_exempt
def telegram_login(request):
    """Оптимизированная авторизация через Telegram"""
    try:
        init_data = request.POST.get('initData')
        logger.debug("telegram_login: initData raw = %r", init_data)
        
        if not init_data:
            logger.error("telegram_login: Нет initData")
            return JsonResponse({'status': 'error', 'error': 'Нет initData'}, status=400)

        # Токен бота из конфигурации
        from ework_config.utils import get_config
        config = get_config()
        bot_token = config.bot_token

        if not verify_init_data(init_data, bot_token):
            logger.error("telegram_login: Неправильная подпись initData")
            return JsonResponse({'status': 'error', 'error': 'Неправильная подпись initData'}, status=403)

        decoded = unquote(init_data)
        params = dict(parse_qsl(decoded, keep_blank_values=True))
        user_data = json.loads(params.get('user', '{}'))
        telegram_id = user_data.get('id')

        auth_date = int(params.get('auth_date', '0'))
        if timezone.now().timestamp() - auth_date > 600:
            logger.error("telegram_login: Истёк auth_date")
            return JsonResponse({'status': 'error', 'error': 'Истёк auth_date'}, status=403)

        if not telegram_id:
            logger.error("telegram_login: Отсутствует Telegram ID в данных")
            return JsonResponse({'status': 'error', 'error': 'Отсутствует Telegram ID'}, status=400)

        # Создаем или обновляем пользователя
        user, created = User.objects.get_or_create(
            telegram_id=telegram_id,
            defaults={
                'first_name': user_data.get('first_name', ''),
                'last_name': user_data.get('last_name', ''),
                'username': user_data.get('username', f"tg_{telegram_id}"),
                'photo_url': user_data.get('photo_url', ''),
            }
        )
        
        if not created:
            # Обновляем данные существующего пользователя
            user.first_name = user_data.get('first_name', '')
            user.last_name = user_data.get('last_name', '')
            user.username = user_data.get('username', f"tg_{telegram_id}")
            if 'photo_url' in user_data:
                user.photo_url = user_data['photo_url']
            user.save(update_fields=['first_name', 'last_name', 'username', 'photo_url'])

        login(request, user)
        return redirect('core:home')

    except Exception:
        logger.exception("telegram_login: Внутренняя ошибка")
        return redirect('users:telegram_auth')


@method_decorator(login_required(login_url='users:telegram_auth'), name='dispatch')
class CreateRatingView(TemplateView):
    """Создание отзыва пользователю"""
    template_name = 'user_ework/rating_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_id = kwargs.get('user_id')
        context['to_user'] = get_object_or_404(User, id=user_id)
        
        # Проверяем, не оставлял ли уже отзыв
        from .models import UserRating
        existing_rating = UserRating.objects.filter(
            from_user=self.request.user,
            to_user=context['to_user']
        ).first()
        
        context['existing_rating'] = existing_rating
        context['can_rate'] = not existing_rating and context['to_user'] != self.request.user
        
        if context['can_rate']:
            context['form'] = UserRatingForm(
                from_user=self.request.user,
                to_user=context['to_user']
            )
        
        return context
    
    def post(self, request, *args, **kwargs):
        user_id = kwargs.get('user_id')
        to_user = get_object_or_404(User, id=user_id)
        
        # Проверяем права
        if to_user == request.user:
            return JsonResponse({'success': False, 'error': 'Нельзя оценивать себя'})
        
        from .models import UserRating
        existing_rating = UserRating.objects.filter(
            from_user=request.user,
            to_user=to_user
        ).first()
        
        if existing_rating:
            return JsonResponse({'success': False, 'error': 'Вы уже оценивали этого пользователя'})
        
        form = UserRatingForm(
            request.POST,
            from_user=request.user,
            to_user=to_user
        )
        
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True, 'message': 'Отзыв добавлен!'})
        else:
            return JsonResponse({'success': False, 'errors': form.errors})