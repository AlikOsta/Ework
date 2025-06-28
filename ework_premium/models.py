from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from datetime import timedelta, datetime
from django.utils import timezone
import uuid
from ework_currency.models import Currency

User = get_user_model()

class Package(models.Model):
    """
    Описывает тарифный пакет (Классика, Старт, Оптимальный, Премиум, Баннер).
    """

    PACKAGE_TYPES = [
        ('FREE_WEEKLY', _('Бесплатная публикация')),
        ('PAID', _('Платная публикация')),
    ]

    name = models.CharField(max_length=50, unique=True, verbose_name=_("Название тарифа"), help_text=_("Название тарифа"))
    description = models.TextField(verbose_name=_("Описание тарифа"), help_text=_("Описание тарифа"))
    package_type = models.CharField(_('Тип пакета'), max_length=20, choices=PACKAGE_TYPES, default='FREE_WEEKLY', help_text=_("Тип пакета"))
    price_per_post = models.DecimalField(max_digits=8, decimal_places=2, verbose_name=_("Цена за объявление"), help_text=_("Цена за объявление"))
    currency = models.ForeignKey(Currency, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("Валюта"), help_text=_("Валюта"))
    
    # Поля для аддонов продвижения
    photo_addon_price = models.DecimalField(max_digits=8, decimal_places=2, default=0, verbose_name=_("Цена за фото"), help_text=_("Цена аддона 'Фото' (30 дней)"))
    highlight_addon_price = models.DecimalField(max_digits=8, decimal_places=2, default=0, verbose_name=_("Цена за выделение"), help_text=_("Цена аддона 'Цветное выделение' (3 дня)"))
    auto_bump_addon_price = models.DecimalField(max_digits=8, decimal_places=2, default=0, verbose_name=_("Цена за автоподнятие"), help_text=_("Цена аддона 'Автоподнятие' (7 дней)"))
    
    # Настройки отображения
    highlight_color = models.CharField(max_length=7, blank=True, default="#fffacd", verbose_name=_("HEX-код цвета для выделения объявления"), help_text=_("HEX-код цвета для выделения объявления"))
    
    duration_days = models.PositiveIntegerField(default=30, verbose_name=_("Срок размещения (дней)"))
    is_active = models.BooleanField(default=True, verbose_name=_("Активен"))
    order = models.SmallIntegerField(default=0, db_index=True, verbose_name=_("Порядок"), help_text=_("Порядок"))

    class Meta:
        verbose_name = _("Тарифный пакет")
        verbose_name_plural = _("Тарифные пакеты")
        ordering = ['order']

    def __str__(self):
        return self.name

    def is_free(self):
        """Проверить, является ли тариф бесплатным"""
        return self.package_type == 'FREE_WEEKLY'

    def is_paid(self):
        """Проверить, является ли тариф платным"""
        return self.package_type == 'PAID'


class Payment(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('pending', _('Ожидает оплаты')),
        ('paid', _('Оплачено')),
        ('failed', _('Ошибка оплаты')),
        ('cancelled', _('Отменено')),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_("Пользователь"))
    package = models.ForeignKey(Package, on_delete=models.CASCADE, verbose_name=_("Тариф"))
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Сумма"))
    order_id = models.CharField(max_length=100, unique=True, verbose_name=_("ID заказа"))
    status = models.CharField(max_length=10, choices=PAYMENT_STATUS_CHOICES, default="pending", verbose_name=_("Статус"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Дата создания"))
    paid_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Дата оплаты"))
    telegram_payment_charge_id = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("ID платежа Telegram"))
    telegram_provider_payment_charge_id = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("ID платежа провайдера"))
    
    # Информация о выбранных аддонах (JSON)
    addons_data = models.JSONField(default=dict, blank=True, verbose_name=_("Данные аддонов"), 
                                  help_text=_("JSON с информацией о выбранных аддонах"))
    
    # Ссылка на пост (черновик)
    post = models.ForeignKey('ework_post.AbsPost', on_delete=models.CASCADE, null=True, blank=True, 
                            verbose_name=_("Пост"), help_text=_("Пост-черновик для публикации после оплаты"))

    class Meta:
        verbose_name = _("Платеж")
        verbose_name_plural = _("Платежи")
        ordering = ['-created_at']

    def __str__(self):
        try:
            username = self.user.username if hasattr(self, 'user') and self.user else 'Unknown'
            return f"Платеж {self.order_id} - {username}"
        except:
            return f"Платеж {self.order_id}"

    @classmethod
    def generate_order_id(cls, user_id):
        """Генерировать уникальный ID заказа"""
        return f"{user_id}_{int(timezone.now().timestamp())}_{uuid.uuid4().hex[:8]}"

    def mark_as_paid(self, telegram_charge_id=None, provider_charge_id=None):
        """Отметить платеж как оплаченный"""
        self.status = 'paid'
        self.paid_at = timezone.now()
        if telegram_charge_id:
            self.telegram_payment_charge_id = telegram_charge_id
        if provider_charge_id:
            self.telegram_provider_payment_charge_id = provider_charge_id
        self.save(update_fields=['status', 'paid_at', 'telegram_payment_charge_id', 'telegram_provider_payment_charge_id'])

    def mark_as_failed(self):
        """Отметить платеж как неудачный"""
        self.status = 'failed'
        self.save(update_fields=['status'])

    def get_payload(self):
        """Получить payload для Telegram"""
        return f"{self.user.telegram_id}&&&{self.id}"
    
    def set_addons(self, photo=False, highlight=False, auto_bump=False):
        """Установить информацию о выбранных аддонах"""
        self.addons_data = {
            'photo': photo,
            'highlight': highlight,
            'auto_bump': auto_bump
        }
    
    def has_photo_addon(self):
        """Проверить, выбран ли аддон фото"""
        return self.addons_data.get('photo', False)
    
    def has_highlight_addon(self):
        """Проверить, выбран ли аддон выделения"""
        return self.addons_data.get('highlight', False)
    
    def has_auto_bump_addon(self):
        """Проверить, выбран ли аддон автоподнятия"""
        return self.addons_data.get('auto_bump', False)


class FreePostRecord(models.Model):
    """
    Отмечает, что пользователь использовал бесплатное размещение на текущей неделе.
    """
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='free_posts')
    week_start = models.DateField(help_text="Дата понедельника этой недели")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Дата создания")) 
    post = models.ForeignKey('ework_post.AbsPost', on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        verbose_name = _("Бесплатная публикация")
        verbose_name_plural = _("Бесплатные публикации")
        unique_together = ['user', 'week_start'] 

    def __str__(self):
        return f"{self.user.username} - {self.week_start}"
    
    @classmethod
    def get_current_week_start(cls):
        """Получить дату начала текущей недели (понедельник)"""
        today = timezone.now().date()
        days_since_monday = today.weekday()
        return today - timedelta(days=days_since_monday)

    @classmethod
    def can_user_post_free(cls, user):
        """Проверить, может ли пользователь опубликовать бесплатно на этой неделе"""
        week_start = cls.get_current_week_start()
        return not cls.objects.filter(user=user, week_start=week_start).exists()
    
    @classmethod
    def use_free_post(cls, user, post):
        """Отметить использование бесплатной публикации"""
        week_start = cls.get_current_week_start()
        record, created = cls.objects.get_or_create(
            user=user,
            week_start=week_start,
            defaults={'post': post}
        )
        if not created and not record.post:
            record.post = post
            record.save(update_fields=['post'])
        return record

    @classmethod
    def get_user_free_post_this_week(cls, user):
        """Получить запись о бесплатной публикации пользователя на этой неделе"""
        week_start = cls.get_current_week_start()
        try:
            return cls.objects.get(user=user, week_start=week_start)
        except cls.DoesNotExist:
            return None
