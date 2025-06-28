from django.db import models
from django.core.exceptions import ValidationError


class SiteConfig(models.Model):
    """
    Модель для хранения всех настроек сайта и бота
    Должна быть singleton - только одна запись
    """
    
    # Основные настройки сайта
    site_name = models.CharField(max_length=200, default='eWork', verbose_name='Название сайта')
    site_description = models.TextField(default='Платформа для поиска работы и услуг', verbose_name='Описание сайта')
    site_url = models.URLField(default='https://localhost:8000', verbose_name='URL сайта')
    
    # Telegram Bot настройки
    bot_token = models.CharField(max_length=200, verbose_name='Bot Token', blank=True)
    bot_username = models.CharField(max_length=100, verbose_name='Bot Username', blank=True)
    
    # Telegram Notification Bot (для уведомлений админам)
    notification_bot_token = models.CharField(max_length=200, verbose_name='Notification Bot Token', blank=True)
    admin_chat_id = models.CharField(max_length=50, verbose_name='Admin Chat ID', blank=True)
    
    # Payment настройки
    payment_provider_token = models.CharField(max_length=200, verbose_name='Payment Provider Token', blank=True)
    
    # AI API настройки
    mistral_api_key = models.CharField(max_length=200, verbose_name='Mistral API Key', blank=True)
    
    # Настройки модерации
    auto_moderation_enabled = models.BooleanField(
        default=True, 
        verbose_name='Автоматическая модерация включена',
        help_text='Использовать ИИ для автоматической проверки постов'
    )
    manual_approval_required = models.BooleanField(
        default=False, 
        verbose_name='Требуется ручное одобрение',
        help_text='Даже после ИИ модерации требуется ручное одобрение админом'
    )
    
    # Настройки постов
    max_free_posts_per_user = models.PositiveIntegerField(default=3, verbose_name='Максимум бесплатных постов на пользователя')
    post_expiry_days = models.PositiveIntegerField(default=30, verbose_name='Дни до истечения поста')
    
    # Настройки рейтинга
    min_rating_to_post = models.FloatField(default=0.0, verbose_name='Минимальный рейтинг для публикации')
    
    # Email настройки
    contact_email = models.EmailField(blank=True, verbose_name='Контактный email')
    support_email = models.EmailField(blank=True, verbose_name='Email поддержки')
    
    # Социальные сети
    telegram_channel = models.CharField(max_length=100, blank=True, verbose_name='Telegram канал')
    telegram_group = models.CharField(max_length=100, blank=True, verbose_name='Telegram группа')
    
    # SEO настройки
    meta_keywords = models.TextField(blank=True, verbose_name='Meta keywords')
    meta_description = models.TextField(blank=True, verbose_name='Meta description')
    
    # Технические настройки
    debug_mode = models.BooleanField(default=False, verbose_name='Режим отладки')
    maintenance_mode = models.BooleanField(default=False, verbose_name='Режим обслуживания')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлено')
    
    class Meta:
        verbose_name = 'Конфигурация сайта'
        verbose_name_plural = 'Конфигурация сайта'
    
    def save(self, *args, **kwargs):
        # Обеспечиваем singleton паттерн
        if not self.pk and SiteConfig.objects.exists():
            raise ValidationError('Может существовать только одна конфигурация сайта')
        return super().save(*args, **kwargs)
    
    def __str__(self):
        return f'Конфигурация {self.site_name}'
    
    @classmethod
    def get_config(cls):
        """Получить единственную конфигурацию или создать с дефолтными значениями"""
        config, created = cls.objects.get_or_create(pk=1)
        return config


class AdminUser(models.Model):
    """Модель для хранения админов с их правами"""
    
    telegram_id = models.BigIntegerField(unique=True, verbose_name='Telegram ID')
    username = models.CharField(max_length=100, blank=True, verbose_name='Username')
    first_name = models.CharField(max_length=100, blank=True, verbose_name='Имя')
    last_name = models.CharField(max_length=100, blank=True, verbose_name='Фамилия')
    
    # Права доступа
    can_moderate_posts = models.BooleanField(default=True, verbose_name='Может модерировать посты')
    can_manage_users = models.BooleanField(default=False, verbose_name='Может управлять пользователями')
    can_manage_payments = models.BooleanField(default=False, verbose_name='Может управлять платежами')
    can_view_analytics = models.BooleanField(default=True, verbose_name='Может просматривать аналитику')
    can_manage_config = models.BooleanField(default=False, verbose_name='Может изменять конфигурацию')
    
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создан')
    
    class Meta:
        verbose_name = 'Администратор'
        verbose_name_plural = 'Администраторы'
    
    def __str__(self):
        name = self.first_name or self.username or str(self.telegram_id)
        return f'Админ: {name}'


class SystemLog(models.Model):
    """Модель для логирования системных событий"""
    
    LOG_LEVELS = [
        ('DEBUG', 'Debug'),
        ('INFO', 'Info'),
        ('WARNING', 'Warning'),
        ('ERROR', 'Error'),
        ('CRITICAL', 'Critical'),
    ]
    
    level = models.CharField(max_length=20, choices=LOG_LEVELS, default='INFO', verbose_name='Уровень')
    message = models.TextField(verbose_name='Сообщение')
    module = models.CharField(max_length=100, blank=True, verbose_name='Модуль')
    user_id = models.BigIntegerField(null=True, blank=True, verbose_name='ID пользователя')
    extra_data = models.JSONField(null=True, blank=True, verbose_name='Дополнительные данные')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')
    
    class Meta:
        verbose_name = 'Системный лог'
        verbose_name_plural = 'Системные логи'
        ordering = ['-created_at']
    
    def __str__(self):
        return f'[{self.level}] {self.message[:50]}...'
