from urllib.parse import parse_qsl, unquote
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import TemplateView, UpdateView, ListView
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
from .forms import UserProfileForm
from django.views.decorators.csrf import csrf_exempt
from django.utils import translation


logger = logging.getLogger(__name__)

User = get_user_model()


@method_decorator(login_required(login_url='user:telegram_auth'), name='dispatch')
class AuthorProfileView(ListView):
    """Представление профиля автора с его объявлениями"""
    model = AbsPost
    template_name = 'user_ework/author_profile.html'
    context_object_name = 'posts'
    paginate_by = 20
    
    def setup(self, request, *args, **kwargs):
        """Инициализация общих данных при настройке представления"""
        super().setup(request, *args, **kwargs)
        self._author = None
        self._is_own_profile = None
        self._posts_by_status = None

    def get_author(self):
        """Получает автора с кэшированием"""
        if self._author is None:
            self._author = get_object_or_404(User, id=self.kwargs['author_id'])
        return self._author
    
    def get_template_names(self):
        if self.request.headers.get('HX-Request') == 'true':
            return ['user_ework/author_profile.html']
        else:
            return ['user_ework/author_profile_full.html']
    
    def is_own_profile(self):
        """Проверяет, является ли профиль собственным (с кэшированием результата)"""
        if self._is_own_profile is None:
            try:
                self._is_own_profile = self.request.user.is_authenticated and self.request.user.id == self.get_author().id
                logger.info(f"Is own profile: {self._is_own_profile}")
            except Exception as e:
                logger.error(f"Error checking if own profile: {e}")
                self._is_own_profile = False
        return self._is_own_profile

    def get_posts_by_status(self):
        """Получает посты автора, сгруппированные по статусам"""
        if self._posts_by_status is None:
            author = self.get_author()
            is_own = self.is_own_profile()
            
            # Базовый queryset для всех постов автора
            base_queryset = AbsPost.objects.filter(
                user=author,
                is_deleted=False  # Исключаем удаленные посты
            ).select_related('user', 'city', 'currency', 'sub_rubric').order_by('-created_at')
            
            if is_own:
                # Для собственного профиля получаем посты всех статусов
                self._posts_by_status = {
                    'published': list(base_queryset.filter(status=3)),  # Опубликованные
                    'pending': list(base_queryset.filter(status=0)),    # На модерации (не проверено)
                    'approved': list(base_queryset.filter(status=1)),   # Одобрено, но не опубликовано
                    'rejected': list(base_queryset.filter(status=2)),   # Заблокированные
                    'archived': list(base_queryset.filter(status=4)),   # В архиве
                }
            else:
                # Для чужого профиля показываем только опубликованные
                self._posts_by_status = {
                    'published': list(base_queryset.filter(status=3)),
                    'pending': [],
                    'approved': [],
                    'rejected': [],
                    'archived': [],
                }
        
        return self._posts_by_status

    def get_queryset(self):
        """Получает объявления для основного списка (опубликованные)"""
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
            
            # Дополнительная статистика профиля
            if is_own_profile:
                context.update({
                    'profile_stats': self.get_profile_stats(author, posts_by_status),
                })
            
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
        """Получает дополнительную статистику профиля"""
        try:
            from ework_post.models import PostView
            from django.contrib.contenttypes.models import ContentType
            from django.db.models import Count, Sum
            
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
                # Подсчет просмотров
                post_ids = [post.pk for post in all_posts]
                content_types = ContentType.objects.get_for_models(*[type(post) for post in all_posts]).values()
                
                total_views = PostView.objects.filter(
                    content_type__in=content_types,
                    object_id__in=post_ids
                ).count()
                
                # Подсчет избранных
                total_favorites = Favorite.objects.filter(post__in=all_posts).count()
                
                # Средняя цена (только для опубликованных)
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


def profile_edit(request):
    """Функция-представление для редактирования профиля"""
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            user = form.save()
            
            # Обрабатываем смену языка
            new_language = form.cleaned_data.get('language')
            if new_language and new_language != request.LANGUAGE_CODE:
                # Сохраняем язык в сессии
                request.session[translation.LANGUAGE_SESSION_KEY] = new_language
                # Активируем новый язык
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
    try:
        init_data = request.POST.get('initData')
        logger.debug("telegram_login: initData raw = %r", init_data)
        if not init_data:
            logger.error("telegram_login: Нет initData")
            return JsonResponse({'status': 'error', 'error': 'Нет initData'}, status=400)

        bot_token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
        print(bot_token)

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

        user, created = User.objects.get_or_create(telegram_id=telegram_id)
        user.first_name = user_data.get('first_name', '')
        user.last_name = user_data.get('last_name', '')
        user.username = user_data.get('username', f"tg_{telegram_id}")
        if 'photo_url' in user_data:
            user.photo_url = user_data['photo_url']
        user.save()

        login(request, user)

        return redirect('core:home')

    except Exception:
        logger.exception("telegram_login: Внутренняя ошибка")
        return redirect('user:telegram_auth')
