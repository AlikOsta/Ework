from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from datetime import timedelta, datetime
from django.utils import timezone

User = get_user_model()

class Package(models.Model):
    """
    Описывает тарифный пакет (Классика, Старт, Оптимальный, Премиум, Баннер).
    """

    PACKAGE_TYPES = [
        ('FREE_WEEKLY', _('Бесплатная публикация')),
        ('STANDARD', _('Стандартная публикация')),
        ('PREMIUM_PHOTO', _('Публикация с фото')),
    ]

    name = models.CharField(max_length=50, unique=True, verbose_name=_("Название тарифа"), help_text=_("Название тарифа"))
    package_type = models.CharField(_('Тип пакета'), max_length=20, choices=PACKAGE_TYPES, default='FREE_WEEKLY', help_text=_("Тип пакета"))
    description = models.TextField(verbose_name=_("Описание тарифа"), help_text=_("Описание тарифа"))
    price_per_post = models.DecimalField(max_digits=8, decimal_places=2, verbose_name=_("Цена за объявление"), help_text=_("Цена за объявление"))
    highlight_color = models.CharField(max_length=7, blank=True,verbose_name=_("HEX-код цвета для выделения объявления"), help_text=_("HEX-код цвета для выделения объявления"))
    icon_flag = models.CharField(max_length=50, blank=True, verbose_name=_("Имя CSS-класса или значка (например, ⭐️ для Премиум)"), help_text=_("Имя CSS-класса или значка (например, ⭐️ для Премиум)"))
    allows_photo = models.BooleanField(default=False, verbose_name=_("Разрешены фото"))
    duration_days = models.PositiveIntegerField(default=30, verbose_name=_("Срок размещения (дней)"))
    is_active = models.BooleanField(default=True, verbose_name=_("Активен"))
    order = models.SmallIntegerField(default=0, db_index=True, verbose_name=_("Порядок"), help_text=_("Порядок"))

    class Meta:
        verbose_name = _("Тарифный пакет")
        verbose_name_plural = _("Тарифные пакеты")
        ordering = ['order']

    def __str__(self):
        return self.name

class PostPayment(models.Model):
    """Оплата за конкретное объявление"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.OneToOneField('ework_post.AbsPost', on_delete=models.CASCADE)
    package = models.ForeignKey(Package, on_delete=models.CASCADE)
    payment_transaction = models.ForeignKey("PaymentTransaction", on_delete=models.SET_NULL, null=True)
    is_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField( auto_now_add=True,  db_index=True,  verbose_name=_("Дата создания")) 


class PaymentTransaction(models.Model):
    """История платежных транзакций"""
    
    STATUS_CHOICES = [
        ('PENDING', _('Ожидает оплаты')),
        ('PROCESSING', _('Обрабатывается')),
        ('COMPLETED', _('Завершена')),
        ('FAILED', _('Ошибка')),
        ('CANCELLED', _('Отменена')),
        ('REFUNDED', _('Возвращена')),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    package = models.ForeignKey(Package, on_delete=models.CASCADE)
    amount = models.DecimalField(_('Сумма'), max_digits=10, decimal_places=2)
    currency = models.CharField(_('Валюта'), max_length=3)
    status = models.CharField(_('Статус'), max_length=20, choices=STATUS_CHOICES, default='PENDING')
    telegram_payment_charge_id = models.CharField(_('Telegram Payment ID'), max_length=255, blank=True)
    provider_payment_charge_id = models.CharField(_('Provider Payment ID'), max_length=255, blank=True)
    invoice_payload = models.TextField(_('Payload инвойса'), blank=True)
    telegram_data = models.JSONField(_('Данные от Telegram'), default=dict, blank=True)
    created_at = models.DateTimeField( auto_now_add=True,  db_index=True,  verbose_name=_("Дата создания")) 
    completed_at = models.DateTimeField(_('Завершена'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('Платежная транзакция')
        verbose_name_plural = _('Платежные транзакции')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.amount} {self.currency} ({self.status})"
    
    def mark_completed(self, telegram_data=None):
        """Отметить транзакцию как завершенную"""
        self.status = 'COMPLETED'
        self.completed_at = timezone.now()
        if telegram_data:
            self.telegram_data = telegram_data
        self.save()


class FreePostRecord(models.Model):
    """
    Отмечает, что пользователь использовал бесплатное размещение на текущей неделе.
    """
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='free_posts')
    week_start = models.DateField(help_text="Дата понедельника этой недели")
    created_at = models.DateTimeField( auto_now_add=True,  db_index=True,  verbose_name=_("Дата создания")) 
    post = models.ForeignKey('ework_post.AbsPost', on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        unique_together = ('user', 'week_start')
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
        record, created = cls.objects.get_or_create(
            user=user,
            week_start=week_start,
            defaults={'used_at': None}
        )
        return record.used_at is None
    
    @classmethod
    def use_free_post(cls, user, post):
        """Отметить использование бесплатной публикации"""
        week_start = cls.get_current_week_start()
        record, created = cls.objects.get_or_create(
            user=user,
            week_start=week_start,
            defaults={'used_at': timezone.now(), 'post': post}
        )
        if not record.used_at:
            record.used_at = timezone.now()
            record.post = post
            record.save()
        return record