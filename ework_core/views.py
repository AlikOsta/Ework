from django.contrib import messages 
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _ 
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import ListView, DetailView, View
from django.db.models import Q, Count
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json

from ework_rubric.models import SuperRubric, SubRubric
from ework_post.models import AbsPost, Favorite, BannerPost, PostView
from ework_post.views import BasePostListView
from ework_locations.models import City
from ework_job.choices import EXPERIENCE_CHOICES, WORK_FORMAT_CHOICES, WORK_SCHEDULE_CHOICES
from ework_premium.models import Package


def home(request):
    context = {
        "categories": SuperRubric.objects.order_by('order'),
        "banners": BannerPost.objects.filter(is_active=True).order_by('order')[:5],
    }
    return render(request, "pages/index.html", context)


def modal_select_post(request):
    return render(request, 'includes/modal_select_post.html')


class PostListByRubricView(BasePostListView):
    template_name = 'components/card.html'
    paginate_by = 50

    def dispatch(self, request, *args, **kwargs):
        self.super_rubric = None
        rubric_pk = self.kwargs.get('rubric_pk')
        if rubric_pk:
            self.super_rubric = SuperRubric.objects.filter(pk=rubric_pk).first()
        self.is_job_category = bool(self.super_rubric and self.super_rubric.slug == 'rabota')
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        qs = super().get_queryset().select_related('user', 'city', 'currency', 'sub_rubric')
        
        # Фильтрация по рубрике
        if self.super_rubric:
            qs = qs.filter(sub_rubric__super_rubric=self.super_rubric)
        
        # Поиск
        search_query = self.request.GET.get('q', '').strip()
        if search_query:
            qs = qs.filter(Q(title__icontains=search_query) | Q(description__icontains=search_query))
        
        # Остальные фильтры
        qs = self.filter_price(qs)
        qs = self.filter_sub_rubric(qs)
        qs = self.filter_city(qs)
        if self.is_job_category:
            qs = self.filter_job(qs)
        
        return self.sort_queryset(qs)

    def filter_price(self, qs):
        price_min = self.request.GET.get('price_min')
        price_max = self.request.GET.get('price_max')
        if price_min and price_min.isdigit():
            qs = qs.filter(price__gte=int(price_min))
        if price_max and price_max.isdigit():
            qs = qs.filter(price__lte=int(price_max))
        return qs

    def filter_sub_rubric(self, qs):
        sub_rubric = self.request.GET.get('sub_rubric')
        if sub_rubric and sub_rubric.isdigit():
            qs = qs.filter(sub_rubric_id=int(sub_rubric))
        return qs

    def filter_city(self, qs):
        city = self.request.GET.get('city')
        if city and city.isdigit():
            qs = qs.filter(city_id=int(city))
        return qs

    def filter_job(self, qs):
        from ework_job.models import PostJob
        job_ids = PostJob.objects.values_list('id', flat=True)
        qs = qs.filter(id__in=job_ids)
        params = {
            'postjob__experience': self.request.GET.get('experience'),
            'postjob__work_format': self.request.GET.get('work_format'),
            'postjob__work_schedule': self.request.GET.get('work_schedule'),
        }
        for field, value in params.items():
            if value and value.isdigit():
                qs = qs.filter(**{field: int(value)})
        return qs

    def sort_queryset(self, qs):
        sort = self.request.GET.get('sort', 'newest')
        ordering = {
            'oldest': 'created_at',
            'price_asc': 'price',
            'price_desc': '-price',
        }.get(sort, '-created_at')
        return qs.order_by(ordering)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Получаем подкатегории для текущей рубрики
        if self.super_rubric:
            context['categories'] = SubRubric.objects.filter(super_rubric=self.super_rubric)
        else:
            context['categories'] = []
        
        # Preserve filters in context
        context.update({
            'search_query': self.request.GET.get('q', ''),
            'price_min': self.request.GET.get('price_min', ''),
            'price_max': self.request.GET.get('price_max', ''),
            'sub_rubric': self.request.GET.get('sub_rubric', ''),
            'selected_city': self.request.GET.get('city', ''),
            'sort': self.request.GET.get('sort', 'newest'),
            'experience': self.request.GET.get('experience', ''),
            'work_format': self.request.GET.get('work_format', ''),
            'work_schedule': self.request.GET.get('work_schedule', ''),
            'cities': City.objects.all(),
            'experience_choices': EXPERIENCE_CHOICES,
            'work_format_choices': WORK_FORMAT_CHOICES,
            'work_schedule_choices': WORK_SCHEDULE_CHOICES,
            'rubric_pk': getattr(self.super_rubric, 'pk', None),
            'category_slug': getattr(self.super_rubric, 'slug', ''),
            'is_job_category': self.is_job_category,
            'is_service_category': bool(self.super_rubric and self.super_rubric.slug == 'uslugi'),
        })
        if self.request.user.is_authenticated:
            fav_ids = Favorite.objects.filter(
                user=self.request.user,
                post__in=context['posts']
            ).values_list('post_id', flat=True)
            context['favorite_post_ids'] = list(fav_ids)
        return context


class PostDetailView(DetailView):
    model = AbsPost
    template_name = 'includes/post_detail.html'
    context_object_name = 'post'

    def get_queryset(self):
        return AbsPost.objects.select_related('user', 'city', 'currency', 'sub_rubric')

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if self.request.user.is_authenticated and obj.user_id != self.request.user.id:
            ct = ContentType.objects.get_for_model(obj)
            PostView.objects.get_or_create(
                user=self.request.user,
                content_type=ct,
                object_id=obj.pk,
                defaults={'created_at': timezone.now()}
            )
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        stats = PostView.objects.filter(
            content_type=ContentType.objects.get_for_model(self.object),
            object_id=self.object.pk
        ).aggregate(
            total_views=Count('id'),
            unique_viewers=Count('user', distinct=True)
        )
        context.update({
            'view_count': stats['total_views'],
            'unique_viewers': stats['unique_viewers'],
            'is_favorite': False,
            'favorite_post_ids': []
        })
        if self.request.user.is_authenticated:
            fav = Favorite.objects.filter(
                user=self.request.user,
                post=self.object
            ).exists()
            context['is_favorite'] = fav
            context['favorite_post_ids'] = [self.object.pk] if fav else []
        return context


class FavoriteListView(ListView):
    model = AbsPost
    template_name = 'pages/favorites.html'
    context_object_name = 'posts'

    def get_queryset(self):
        return AbsPost.objects.filter(
            favorited_by__user=self.request.user,
            status=3
        ).select_related('city','currency','user').prefetch_related('favorited_by').distinct()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        total = self.get_queryset().count()
        ctx.update({
            'title': 'Избранное',
            'has_more': total > len(ctx['posts']),
        })
        return ctx


@require_POST
def toggle_favorite(request, post_pk):
    post = get_object_or_404(AbsPost, pk=post_pk)
    fav, created = Favorite.objects.get_or_create(user=request.user, post=post)
    if not created:
        fav.delete()
        is_favorite = False
    else:
        is_favorite = True

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'is_favorite': is_favorite,
            'post_id': post.pk
        })
    
    return redirect('core:post_list_by_rubric', rubric_pk=post.sub_rubric.super_rubric.pk)



def banner_view(request, banner_id):
    banner = get_object_or_404(BannerPost, id=banner_id)
    return render(request, 'includes/banner_view.html', {'banner': banner})


def banner_ad_info(request):
    return render(request, 'includes/banner_ad_modal.html', {'admin_telegram': '@newpunknot'})


def premium(request):
    packages = Package.objects.filter(is_active=True).order_by('order')
    context = {
        'packages': packages
    }
    return render(request, 'pages/premium.html', context)


def get_post_views_stats(post):
    ct = ContentType.objects.get_for_model(post)
    stats = PostView.objects.filter(content_type=ct, object_id=post.pk).aggregate(
        total_views=Count('id'),
        unique_viewers=Count('user', distinct=True)
    )
    return stats


class CreateInvoiceView(View):
    """API для создания инвойса через Telegram Bot"""
    
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            payment_id = data.get('payment_id')
            if not payment_id:
                return JsonResponse({'success': False, 'error': 'payment_id обязателен'}, status=400)

            from ework_premium.models import Payment
            try:
                payment = Payment.objects.get(
                    id=payment_id,
                    user=request.user,
                    status='pending'
                )
            except Payment.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Платеж не найден'}, status=404)

            if not request.user.telegram_id:
                return JsonResponse({'success': False, 'error': 'У пользователя не задан telegram_id'}, status=400)

            payload     = payment.get_payload()
            amount      = payment.amount
            order_id    = payment.order_id
            addons_data = payment.addons_data

            # Создаём инвойс-ссылку
            from ework_bot_tg.bot.bot import create_invoice_link
            invoice_link = create_invoice_link(
                user_id=request.user.telegram_id,
                payment_id=payment.id,
                payload=payload,
                amount=amount,
                order_id=order_id,
                addons_data=addons_data
            )

            if not invoice_link:
                return JsonResponse({'success': False, 'error': 'Ошибка создания инвойса'}, status=500)

            return JsonResponse({'success': True, 'invoice_link': invoice_link})

        except Exception as e:
            # Логируем полную трассировку
            import traceback; traceback.print_exc()
            return JsonResponse({'success': False, 'error': f'Внутренняя ошибка: {e}'}, status=500)


def publish_post_after_payment(user_id, payment_id):
    """Функция для публикации поста после успешной оплаты (вызывается из бота)"""
    try:
        from ework_premium.models import Payment
        
        print(f"🔧 Обрабатываем платеж {payment_id} для пользователя {user_id}")
        
        # Получаем платеж
        payment = Payment.objects.select_related('user').get(
            id=payment_id,
            user__telegram_id=user_id,
            status='pending'
        )
        
        print(f"🔧 Платеж найден: ID={payment.id}, Order={payment.order_id}")
        
        # Проверяем, есть ли связанный пост
        if not payment.post:
            print(f"❌ Нет поста для платежа {payment_id}")
            payment.mark_as_paid()
            return False
        
        post = payment.post
        print(f"🔧 Найден пост-черновик: {post.title} (ID: {post.id})")
        
        # Переводим пост из черновика на модерацию
        post.status = 0  # На модерацию
        post.save(update_fields=['status'])
        
        # Отмечаем платеж как оплаченный
        payment.mark_as_paid()
        
        print(f"✅ Платеж {payment_id} обработан, пост {post.id} отправлен на модерацию")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка публикации поста после оплаты: {e}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")
        return False


@login_required
@require_POST
def change_post_status(request, pk, status):
    """Изменение статуса поста"""
    post = get_object_or_404(AbsPost, pk=pk, user=request.user)
    
    # Проверяем допустимые переходы статусов
    allowed_transitions = {
        3: [4],  # Из опубликованного можно перевести в архив
        4: [0],  # Из архива можно отправить на модерацию
    }
    
    if post.status in allowed_transitions and status in allowed_transitions[post.status]:
        post.status = status
        post.save()
        
        status_messages = {
            0: _('Объявление отправлено на модерацию'),
            4: _('Объявление перемещено в архив'),
        }
        
        if status in status_messages:
            messages.success(request, status_messages[status])
    else:
        messages.error(request, _('Недопустимое изменение статуса'))
    
    return redirect('user:author_profile', author_id=request.user.id)


@login_required
def post_edit(request, pk):
    """Редактирование поста"""
    post = get_object_or_404(AbsPost, pk=pk, user=request.user)
    
    try:
        job_post = post.postjob
        return redirect('job:post_edit', pk=pk)
    except:
        pass
    
    try:
        services_post = post.postservices
        return redirect('services:post_edit', pk=pk)
    except:
        pass
    
    messages.error(request, _('Неизвестный тип объявления'))
    return redirect('user:author_profile', author_id=request.user.id)



@login_required
def post_delete_confirm(request, pk):
    """Подтверждение удаления поста"""
    post = get_object_or_404(AbsPost, pk=pk, user=request.user)
    
    if request.method == 'POST':
        post.is_deleted = True
        post.save()
        messages.success(request, _('Объявление успешно удалено'))
        
        if request.headers.get('HX-Request'):
            return HttpResponse(
                status=200,
                headers={'HX-Redirect': reverse('user:author_profile', kwargs={'author_id': request.user.id})}
            )
        return redirect('user:author_profile', author_id=request.user.id)
    
    return render(request, 'includes/post_delete_confirm.html', {'post': post})
