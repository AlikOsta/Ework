from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DetailView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.db.models import Q, Count
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError

from ework_post.models import AbsPost, Favorite, PostView
from ework_rubric.models import SuperRubric, SubRubric
from ework_premium.models import Package, FreePostRecord
from ework_premium.utils import create_payment_for_post


class BasePostListView(ListView):
    """Оптимизированное базовое представление для списка объявлений"""
    model = AbsPost
    template_name = 'components/card.html'
    context_object_name = 'posts'
    paginate_by = 20
    
    def get_queryset(self):
        """Получить отфильтрованный queryset с оптимизированными запросами"""
        queryset = self.model.objects.filter(
            status=3,  # Опубликовано
            is_deleted=False
        ).select_related(
            'user', 'city', 'currency', 'sub_rubric', 'sub_rubric__super_rubric'
        ).prefetch_related('favorited_by')
        
        # Поиск
        search_query = self.request.GET.get('q', '').strip()
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) | 
                Q(description__icontains=search_query)
            )
        
        # Фильтрация по рубрике
        rubric_pk = self.kwargs.get('rubric_pk')
        if rubric_pk:
            queryset = queryset.filter(sub_rubric__super_rubric_id=rubric_pk)
        
        # Фильтрация по подрубрике
        sub_rubric = self.request.GET.get('sub_rubric')
        if sub_rubric and sub_rubric.isdigit():
            queryset = queryset.filter(sub_rubric_id=int(sub_rubric))
        
        # Фильтрация по цене
        price_min = self.request.GET.get('price_min')
        price_max = self.request.GET.get('price_max')
        if price_min and price_min.isdigit():
            queryset = queryset.filter(price__gte=int(price_min))
        if price_max and price_max.isdigit():
            queryset = queryset.filter(price__lte=int(price_max))
        
        # Фильтрация по городу
        city = self.request.GET.get('city')
        if city and city.isdigit():
            queryset = queryset.filter(city_id=int(city))
        
        # Сортировка
        sort_type = self.request.GET.get('sort', 'newest')
        sort_options = {
            'newest': '-created_at',
            'oldest': 'created_at',
            'price_asc': 'price',
            'price_desc': '-price',
        }
        ordering = sort_options.get(sort_type, '-created_at')
        
        return queryset.order_by(ordering)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Избранные посты для текущего пользователя
        if self.request.user.is_authenticated:
            favorite_ids = Favorite.objects.filter(
                user=self.request.user,
                post__in=context['posts']
            ).values_list('post_id', flat=True)
            context['favorite_post_ids'] = list(favorite_ids)
        else:
            context['favorite_post_ids'] = []
        
        # Сохраняем параметры фильтрации
        context.update({
            'search_query': self.request.GET.get('q', ''),
            'price_min': self.request.GET.get('price_min', ''),
            'price_max': self.request.GET.get('price_max', ''),
            'sub_rubric': self.request.GET.get('sub_rubric', ''),
            'selected_city': self.request.GET.get('city', ''),
            'sort': self.request.GET.get('sort', 'newest'),
        })
            
        return context


class BasePostDetailView(DetailView):
    """Оптимизированное базовое представление для детального просмотра поста"""
    model = AbsPost
    template_name = 'includes/post_detail.html'
    context_object_name = 'post'

    def get_queryset(self):
        """Получить queryset с оптимизированными связями"""
        return AbsPost.objects.select_related(
            'user', 'city', 'currency', 'sub_rubric', 'sub_rubric__super_rubric'
        ).filter(status=3, is_deleted=False)

    def get_object(self, queryset=None):
        """Получить объект и записать просмотр"""
        obj = super().get_object(queryset)
        
        # Записываем просмотр только для авторизованных пользователей
        if (self.request.user.is_authenticated and 
            obj.user_id != self.request.user.id):
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
        
        # Статистика просмотров
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
            is_favorite = Favorite.objects.filter(
                user=self.request.user,
                post=self.object
            ).exists()
            context['is_favorite'] = is_favorite
            context['favorite_post_ids'] = [self.object.pk] if is_favorite else []
        
        return context


class BasePostCreateView(LoginRequiredMixin, CreateView):
    """Оптимизированное базовое представление для создания объявления"""
    template_name = 'post/post_form.html'
    success_message = _('Объявление успешно создано и отправлено на модерацию')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        """Обработка валидной формы"""
        # Получаем аддоны из формы
        addon_photo = form.cleaned_data.get('addon_photo', False)
        addon_highlight = form.cleaned_data.get('addon_highlight', False)
        addon_auto_bump = form.cleaned_data.get('addon_auto_bump', False)
        
        # Получаем пакет по умолчанию
        package = Package.objects.filter(is_active=True, package_type='PAID').first()
        
        # Создаем платеж
        payment = create_payment_for_post(
            user=self.request.user,
            package=package,
            photo=addon_photo,
            highlight=addon_highlight,
            auto_bump=addon_auto_bump
        )
        
        # Если платеж не требуется (бесплатная публикация)
        if payment is None:
            return self._publish_free_post(form)
        else:
            return self._handle_paid_post(form, payment)
    
    def _publish_free_post(self, form):
        """Опубликовать бесплатный пост"""
        try:
            self.object = form.save(commit=False)
            self.object.user = self.request.user
            self.object.status = 0  # На модерацию - это вызовет сигнал модерации
            self.object.save()
            
            # Отметить использование бесплатной публикации
            FreePostRecord.use_free_post(self.request.user, self.object)
            
            messages.success(self.request, self.success_message)
            
            if self.request.headers.get('HX-Request'):
                return HttpResponse(
                    status=200,
                    headers={
                        'HX-Trigger': 'closeModal',
                        'HX-Redirect': str(self.get_success_url())
                    }
                )
            
            return redirect(self.get_success_url())
            
        except ValidationError as e:
            form.add_error(None, e)
            return self.form_invalid(form)

    
    def _handle_paid_post(self, form, payment):
        """Обработать платную публикацию"""
        # Создаем пост-черновик
        post = form.save(commit=False)
        post.user = self.request.user
        post.package = payment.package
        post.status = -1  # Черновик
        
        # Применяем аддоны
        post.set_addons(
            photo=form.cleaned_data.get('addon_photo', False),
            highlight=form.cleaned_data.get('addon_highlight', False),
            auto_bump=form.cleaned_data.get('addon_auto_bump', False)
        )
        
        post.save()
        
        # Связываем платеж с постом
        payment.post = post
        payment.save(update_fields=['post'])
        
        # HTMX запрос
        if self.request.headers.get('HX-Request'):
            return JsonResponse({
                'action': 'payment_required',
                'payment_id': payment.id,
                'amount': str(payment.amount),
                'currency': payment.package.currency.symbol if payment.package.currency else '$',
                'payload': payment.get_payload(),
                'order_id': payment.order_id
            })
        
        return redirect('payments:payment_page', payment_id=payment.id)
    
    def get_success_url(self):
        return reverse_lazy('core:home')


class BasePostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Оптимизированное базовое представление для редактирования объявления"""
    template_name = 'post/post_form.html'
    success_message = _('Объявление успешно обновлено и отправлено на модерацию')
    
    def test_func(self):
        """Проверка прав доступа - только автор может редактировать"""
        post = self.get_object()
        return self.request.user == post.user
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        """Обработка валидной формы при редактировании"""
        # Получаем аддоны из формы
        addon_photo = form.cleaned_data.get('addon_photo', False)
        addon_highlight = form.cleaned_data.get('addon_highlight', False)
        
        # Проверяем, нужна ли оплата
        need_payment = addon_photo or addon_highlight
        
        if need_payment:
            return self._handle_paid_update(form, addon_photo, addon_highlight)
        else:
            return self._handle_free_update(form)
    
    def _handle_free_update(self, form):
        """Обработка бесплатного обновления (без аддонов)"""
        # Сохраняем пост без изменения статуса услуг
        form.instance.status = 0  # На модерацию
        form.save()
        
        messages.success(self.request, self.success_message)
        
        if self.request.headers.get('HX-Request'):
            return HttpResponse(
                status=200,
                headers={
                    'HX-Trigger': 'closeModal',
                    'HX-Redirect': reverse('users:author_profile', kwargs={'author_id': self.request.user.id})
                }
            )
        
        return redirect(self.get_success_url())
    
    def _handle_paid_update(self, form, addon_photo, addon_highlight):
        """Обработка платного обновления (с аддонами)"""
        from ework_premium.utils import create_payment_for_post
        from ework_premium.models import Package
        
        # Получаем пакет по умолчанию
        package = Package.objects.filter(is_active=True, package_type='PAID').first()
        
        # Создаем платеж только для новых аддонов
        payment = create_payment_for_post(
            user=self.request.user,
            package=package,
            photo=addon_photo,
            highlight=addon_highlight,
            existing_post=self.object  # Передаем существующий пост
        )
        
        if payment is None:
            # Если оплата не требуется (например, уже есть активные услуги)
            return self._update_post_with_addons(form, addon_photo, addon_highlight)
        
        # Сохраняем пост
        form.save()
        
        # Связываем платеж с постом
        payment.post = self.object
        payment.save(update_fields=['post'])
        
        # HTMX запрос
        if self.request.headers.get('HX-Request'):
            return JsonResponse({
                'action': 'payment_required',
                'payment_id': payment.id,
                'amount': str(payment.amount),
                'currency': payment.package.currency.symbol if payment.package.currency else '$',
                'payload': payment.get_payload(),
                'order_id': payment.order_id,
                'is_update': True  # Флаг что это обновление
            })
        
        return redirect('payments:payment_page', payment_id=payment.id)
    
    def _update_post_with_addons(self, form, addon_photo, addon_highlight):
        """Обновление поста с применением аддонов без оплаты"""
        # Сохраняем основные изменения
        form.save()
        
        # Применяем аддоны
        if addon_photo or addon_highlight:
            self.object.set_addons(
                photo=addon_photo,
                highlight=addon_highlight
            )
            self.object.save(update_fields=[
                'has_photo_addon', 'has_highlight_addon',
                'photo_expires_at', 'highlight_expires_at', 'is_premium'
            ])
        
        # Отправляем на модерацию
        self.object.status = 0
        self.object.save(update_fields=['status'])
        
        messages.success(self.request, self.success_message)
        
        if self.request.headers.get('HX-Request'):
            return HttpResponse(
                status=200,
                headers={
                    'HX-Trigger': 'closeModal',
                    'HX-Redirect': reverse('users:author_profile', kwargs={'author_id': self.request.user.id})
                }
            )
        
        return redirect(self.get_success_url())
    
    def get_success_url(self):
        return reverse_lazy('users:author_profile', kwargs={'author_id': self.request.user.id})


class PricingCalculatorView(View):
    """HTMX view для динамического расчета стоимости"""
    
    def get(self, request, *args, **kwargs):
        """Рассчитать стоимость на основе выбранных аддонов"""
        from ework_premium.utils import PricingCalculator
        from django.contrib.auth import get_user_model
        
        # Получаем параметры аддонов
        addon_photo = request.GET.get('addon_photo') == 'true'
        addon_highlight = request.GET.get('addon_highlight') == 'true'
        
        # Получаем ID поста для редактирования (если есть)
        post_id = request.GET.get('post_id')
        existing_post = None
        if post_id:
            try:
                existing_post = AbsPost.objects.get(id=post_id, user=request.user)
            except AbsPost.DoesNotExist:
                pass
        
        # Для неавторизованных пользователей создаем временного пользователя
        if request.user.is_authenticated:
            user = request.user
        else:
            User = get_user_model()
            user = User(id=999999)  # Фиктивный пользователь
        
        # Создаем калькулятор
        calculator = PricingCalculator(user)
        
        # Получаем разбивку цен
        breakdown = calculator.get_pricing_breakdown(
            photo=addon_photo,
            highlight=addon_highlight,
            existing_post=existing_post
        )
        
        # Получаем конфигурацию кнопки
        button_config = calculator.get_button_config(
            photo=addon_photo,
            highlight=addon_highlight,
            existing_post=existing_post
        )
        
        # Сериализуем currency объект
        if breakdown.get('currency'):
            breakdown['currency'] = {
                'name': breakdown['currency'].name,
                'symbol': breakdown['currency'].symbol,
                'code': breakdown['currency'].code
            }
        
        return JsonResponse({
            'breakdown': breakdown,
            'button': button_config,
            'show_image_field': addon_photo,
            'is_update': existing_post is not None
        })


class PostPaymentSuccessView(LoginRequiredMixin, View):
    """View для обработки публикации после успешной оплаты"""
    
    def post(self, request, payment_id, *args, **kwargs):
        """Опубликовать пост после успешной оплаты"""
        from ework_premium.models import Payment
        
        try:
            payment = Payment.objects.get(
                id=payment_id,
                user=request.user,
                status='paid'
            )
        except Payment.DoesNotExist:
            return JsonResponse({
                'error': 'Платеж не найден или не оплачен'
            }, status=400)
        
        if not payment.post:
            return JsonResponse({
                'error': 'Пост не найден'
            }, status=400)
        
        try:
            # Переводим пост из черновика на модерацию
            post = payment.post
            post.status = 0  # На модерацию
            
            # Применяем оплаченные аддоны
            post.apply_addons_from_payment(payment)
            
            messages.success(request, _('Объявление успешно опубликовано!'))
            
            return JsonResponse({
                'success': True,
                'post_id': post.id,
                'redirect_url': post.get_absolute_url()
            })
            
        except Exception as e:
            return JsonResponse({
                'error': f'Ошибка при создании объявления: {str(e)}'
            }, status=500)


class PostRestoreFromArchiveView(LoginRequiredMixin, UserPassesTestMixin, View):
    """View для восстановления поста из архива"""
    
    def test_func(self):
        """Проверка прав доступа - только автор может восстанавливать"""
        post = self.get_object()
        return self.request.user == post.user
    
    def get_object(self):
        """Получить пост для восстановления"""
        post_id = self.kwargs.get('post_id')
        return get_object_or_404(AbsPost, id=post_id, status=4, is_deleted=False)  # Статус 4 = архив
    
    def post(self, request, post_id, *args, **kwargs):
        """Восстановить пост из архива"""
        from ework_premium.utils import can_user_restore_from_archive_free, create_payment_for_post
        from ework_premium.models import Package, FreePostRecord
        
        post = self.get_object()
        
        # Проверяем, можно ли восстановить бесплатно
        if can_user_restore_from_archive_free(request.user, post):
            # Восстанавливаем бесплатно
            post.status = 0  # На модерацию
            post.save(update_fields=['status'])
            
            # Отмечаем использование бесплатной публикации
            FreePostRecord.use_free_post(request.user, post)
            
            messages.success(request, _('Объявление восстановлено и отправлено на модерацию'))
            
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
            # Нужна оплата - возвращаем форму с выбором аддонов
            package = Package.objects.filter(is_active=True, package_type='PAID').first()
            
            # Если это HTMX запрос, возвращаем форму оплаты
            if request.headers.get('HX-Request'):
                from ework_premium.utils import PricingCalculator
                
                # Получаем базовые настройки (без аддонов)
                calculator = PricingCalculator(request.user, package)
                breakdown = calculator.get_pricing_breakdown(existing_post=post)
                button_config = calculator.get_button_config(existing_post=post)
                
                return JsonResponse({
                    'action': 'show_restore_form',
                    'post_id': post.id,
                    'post_title': post.title,
                    'breakdown': breakdown,
                    'button': button_config,
                    'has_active_addons': post.has_photo_addon or post.has_highlight_addon
                })
            
            # Обычный запрос - редирект на страницу редактирования
            from django.urls import reverse
            edit_url = reverse('jobs:edit_post', kwargs={'pk': post.id}) if hasattr(post, 'postjob') else reverse('services:edit_post', kwargs={'pk': post.id})
            return redirect(edit_url)


class PostRestoreWithAddonsView(LoginRequiredMixin, UserPassesTestMixin, View):
    """View для восстановления поста из архива с доп. услугами"""
    
    def test_func(self):
        """Проверка прав доступа - только автор может восстанавливать"""
        post = self.get_object()
        return self.request.user == post.user
    
    def get_object(self):
        """Получить пост для восстановления"""
        post_id = self.kwargs.get('post_id')
        return get_object_or_404(AbsPost, id=post_id, status=4, is_deleted=False)  # Статус 4 = архив
    
    def post(self, request, post_id, *args, **kwargs):
        """Восстановить пост с доп. услугами"""
        from ework_premium.utils import create_payment_for_post
        from ework_premium.models import Package
        
        post = self.get_object()
        
        # Получаем выбранные аддоны
        addon_photo = request.POST.get('addon_photo') == 'on'
        addon_highlight = request.POST.get('addon_highlight') == 'on'
        
        package = Package.objects.filter(is_active=True, package_type='PAID').first()
        
        # Создаем платеж
        payment = create_payment_for_post(
            user=request.user,
            package=package,
            photo=addon_photo,
            highlight=addon_highlight,
            existing_post=post
        )
        
        if payment is None:
            # Бесплатное восстановление
            post.status = 0  # На модерацию
            if addon_photo or addon_highlight:
                post.set_addons(photo=addon_photo, highlight=addon_highlight)
            post.save()
            
            messages.success(request, _('Объявление восстановлено и отправлено на модерацию'))
            return redirect('users:author_profile', author_id=request.user.id)
        
        # Нужна оплата
        if request.headers.get('HX-Request'):
            return JsonResponse({
                'action': 'payment_required',
                'payment_id': payment.id,
                'amount': str(payment.amount),
                'currency': payment.package.currency.symbol if payment.package.currency else '$',
                'payload': payment.get_payload(),
                'order_id': payment.order_id,
                'is_restore': True
            })
        
        return redirect('payments:payment_page', payment_id=payment.id)