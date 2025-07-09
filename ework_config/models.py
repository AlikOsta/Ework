from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _ 


class SiteConfig(models.Model):
    """
    Модель для хранения всех настроек сайта и бота
    Должна быть singleton - только одна запись
    """
    
    # Основные настройки сайта
    site_name = models.CharField(max_length=200, default='eWork', verbose_name=_('Название'))
    site_description = models.TextField(default='Платформа для поиска работы и услуг', verbose_name=_('Приветственное  сообщение для бота'))
    site_url = models.URLField(default='https://localhost:8000', verbose_name=_('URL сайта для Мини Апп'))
    
    # Telegram Bot настройки
    bot_token = models.CharField(max_length=200, verbose_name='Bot Token', blank=True)
    bot_username = models.CharField(max_length=100, verbose_name='Bot Username', blank=True)
    
    # Telegram Notification Bot (для уведомлений админам)
    notification_bot_token = models.CharField(max_length=200, verbose_name='Support Bot Token', blank=True)
    admin_chat_id = models.CharField(max_length=20, verbose_name='Admin Chat ID', blank=True)
    admin_username = models.CharField(max_length=20, verbose_name='Admin Username', blank=True)
    
    # Payment настройки
    payment_provider_token = models.CharField(max_length=200, verbose_name='Payment Provider Token', blank=True)
    
    # AI API настройки
    mistral_api_key = models.CharField(max_length=200, verbose_name='Mistral API Key', blank=True)
    
    # Настройки модерации
    auto_moderation_enabled = models.BooleanField(
        default=True, 
        verbose_name=_('Автоматическая модерация включена'),
        help_text='Использовать ИИ для автоматической проверки постов'
    )
    manual_approval_required = models.BooleanField(
        default=False, 
        verbose_name=_('Требуется ручное одобрение'),
        help_text='Даже после ИИ модерации требуется ручное одобрение админом'
    )
    
    # Настройки постов
    max_free_posts_per_user = models.PositiveIntegerField(default=1, verbose_name=_('Максимум бесплатных постов на пользователя'))
    post_expiry_days = models.PositiveIntegerField(default=30, verbose_name=_('Дни до истечения поста'))
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Создано'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Обновлено'))
    
    class Meta:
        app_label = "ework_config"
        verbose_name = _('Конфигурация сайта')
        verbose_name_plural = _('Конфигурация сайта')
    
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

