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


def copy_post_views(from_post, to_post):
    """Копирование статистики просмотров с одного поста на другой"""
    try:
        from_content_type = ContentType.objects.get_for_model(from_post)
        to_content_type = ContentType.objects.get_for_model(to_post)
        
        # Получаем все просмотры старого поста
        old_views = PostView.objects.filter(
            content_type=from_content_type,
            object_id=from_post.pk
        )
        
        # Создаем новые просмотры для нового поста
        new_views = []
        for view in old_views:
            new_views.append(PostView(
                user=view.user,
                content_type=to_content_type,
                object_id=to_post.pk,
                created_at=view.created_at
            ))
        
        # Массовое создание
        if new_views:
            PostView.objects.bulk_create(new_views, ignore_conflicts=True)
            
        return len(new_views)
        
    except Exception as e:
        print(f"Ошибка при копировании просмотров: {e}")
        return 0


class RepublishPostView(LoginRequiredMixin, View):
    """View для переопубликования архивного поста"""
    
    def get(self, request, post_id, *args, **kwargs):
        """Отобразить форму для переопубликации в модальном окне"""
        # Проверяем, что пост архивный и принадлежит пользователю
        try:
            post = AbsPost.objects.exclude(status=5).get(
                id=post_id,
                user=request.user,
                status=4,  # Архивный
                is_deleted=False
            )
        except AbsPost.DoesNotExist:
            messages.error(request, _('Архивный пост не найден'))
            return redirect('users:author_profile', author_id=request.user.id)
        
        # Определяем тип поста и отображаем соответствующую форму
        try:
            job_post = post.postjob
            from ework_job.forms import JobPostForm
            form = JobPostForm(user=request.user, copy_from=post_id)
            form_action = reverse('jobs:job_create') + f'?copy_from={post_id}'
            template_name = 'job/post_job_form.html'
        except:
            try:
                services_post = post.postservices
                from ework_services.forms import ServicesPostForm
                form = ServicesPostForm(user=request.user, copy_from=post_id)
                form_action = reverse('services:services_create') + f'?copy_from={post_id}'
                template_name = 'services/post_services_form.html'
            except:
                messages.error(request, _('Неизвестный тип объявления'))
                return redirect('users:author_profile', author_id=request.user.id)
        
        context = {
            'form': form,
            'form_action': form_action,
            'is_republish': True,
            'original_post': post,
            'modal_title': _('Переопубликовать объявление'),
        }
        
        return render(request, template_name, context)


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
        
        # Поддержка копирования из архивного поста
        copy_from = self.request.GET.get('copy_from')
        if copy_from and copy_from.isdigit():
            kwargs['copy_from'] = int(copy_from)
            
        return kwargs
    
    def form_valid(self, form):
        """Обработка валидной формы"""
        # Проверяем, это переопубликация архивного поста или новый пост
        copy_from_id = self.request.GET.get('copy_from')
        
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
            return self._publish_free_post(form, copy_from_id)
        else:
            return self._handle_paid_post(form, payment, copy_from_id)
    
    def _publish_free_post(self, form, copy_from_id=None):
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

    
    def _handle_paid_post(self, form, payment, copy_from_id=None):
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
        
        # Сохраняем ID старого поста для обработки после оплаты
        if copy_from_id:
            payment.addons_data = payment.addons_data or {}
            payment.addons_data['copy_from_id'] = copy_from_id
        
        # Связываем платеж с постом
        payment.post = post
        payment.save(update_fields=['post', 'addons_data'])
        
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
    
    def _handle_republish(self, old_post_id, new_post):
        """Обработка переопубликации: копирование статистики и удаление старого поста"""
        print(f"🔄 DEBUG: _handle_republish вызван с old_post_id={old_post_id}, new_post_id={new_post.id}")
        try:
            old_post = AbsPost.objects.get(
                id=old_post_id,
                user=self.request.user,
                status=4,  # Архивный
                is_deleted=False
            )
            
            print(f"🔄 DEBUG: Найден старый пост {old_post_id}, статус ДО: {old_post.status}")
            
            # Копируем статистику просмотров
            copied_views = copy_post_views(old_post, new_post)
            
            # Помечаем старый пост как удаленный
            old_post.soft_delete()
            
            print(f"🔄 DEBUG: Переопубликация завершена: скопировано {copied_views} просмотров, старый пост {old_post_id} помечен как удаленный, новый статус: {old_post.status}")
            
        except AbsPost.DoesNotExist:
            print(f"❌ DEBUG: Старый пост {old_post_id} не найден при переопубликации")
        except Exception as e:
            print(f"❌ DEBUG: Ошибка при обработке переопубликации: {e}")
    
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
        """Обработка валидной формы"""
        # При обновлении отправляем на модерацию
        form.instance.status = 0  # Не проверено
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
        addon_auto_bump = request.GET.get('addon_auto_bump') == 'true'
        
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
            auto_bump=addon_auto_bump
        )
        
        # Получаем конфигурацию кнопки
        button_config = calculator.get_button_config(
            photo=addon_photo,
            highlight=addon_highlight,
            auto_bump=addon_auto_bump
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
            'show_image_field': addon_photo
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
            post.save(update_fields=['status'])
            
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