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

    def get_queryset(self):
        """Получает объявления автора"""
        author = self.get_author()
        return AbsPost.objects.filter(
            user=author,  
            status=3  
        ).select_related('user', 'city', 'currency', 'sub_rubric').order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        try:
            context = super().get_context_data(**kwargs)
            author = self.get_author()
            is_own_profile = self.is_own_profile()
            
            context.update({
                'author': author,
                'is_own_profile': is_own_profile,
                'posts_count': self.get_queryset().count(),
            })
            
            if self.request.user.is_authenticated:
                favorite_post_ids = Favorite.objects.filter(
                    user=self.request.user,
                    post__in=context['posts']
                ).values_list('post_id', flat=True)
                context['favorite_post_ids'] = list(favorite_post_ids)
            else:
                context['favorite_post_ids'] = []
            
            return context
            
        except Exception as e:
            logger.error(f"Error in get_context_data: {e}")
            return {
                'author': self.get_author(), 
                'is_own_profile': False,
                'posts': [],
                'posts_count': 0,
                'favorite_post_ids': []
            }


def profile_edit(request):
    """Функция-представление для редактирования профиля"""
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            if request.headers.get('HX-Request'):
                return HttpResponse(
                    status=200,
                    headers={
                        'HX-Trigger': 'closeModal',
                        'HX-Redirect': reverse('user:author_profile', kwargs={'author_id': request.user.id})
                    }
                )
            return redirect('user:author_profile', author_id=request.user.id)
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
