from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.http import HttpResponseRedirect
from .models import SiteConfig, AdminUser, SystemLog


@admin.register(SiteConfig)
class SiteConfigAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Основные настройки сайта', {
            'fields': ('site_name', 'site_description', 'site_url')
        }),
        ('Telegram Bot', {
            'fields': ('bot_token', 'bot_username'),
            'classes': ('collapse',)
        }),
        ('Уведомления', {
            'fields': ('notification_bot_token', 'admin_chat_id'),
            'classes': ('collapse',)
        }),
        ('Платежи', {
            'fields': ('payment_provider_token',),
            'classes': ('collapse',)
        }),
        ('AI и модерация', {
            'fields': ('mistral_api_key', 'auto_moderation_enabled', 'manual_approval_required'),
            'classes': ('collapse',)
        }),
        ('Настройки постов', {
            'fields': ('max_free_posts_per_user', 'post_expiry_days', 'min_rating_to_post'),
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def has_add_permission(self, request):
        # Разрешаем создание только если нет конфигурации
        return not SiteConfig.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Запрещаем удаление конфигурации
        return False
    
    def changelist_view(self, request, extra_context=None):
        # Если конфигурация существует, перенаправляем на её редактирование
        try:
            config = SiteConfig.objects.get(pk=1)
            return HttpResponseRedirect(reverse('admin:ework_config_siteconfig_change', args=[config.pk]))
        except SiteConfig.DoesNotExist:
            return super().changelist_view(request, extra_context)


@admin.register(AdminUser)
class AdminUserAdmin(admin.ModelAdmin):
    list_display = ('telegram_id', 'full_name', 'username', 'permissions_summary', 'is_active', 'created_at')
    list_filter = ('is_active', 'can_moderate_posts', 'can_manage_users', 'can_manage_payments', 'created_at')
    search_fields = ('telegram_id', 'username', 'first_name', 'last_name')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('telegram_id', 'username', 'first_name', 'last_name', 'is_active')
        }),
        ('Права доступа', {
            'fields': ('can_moderate_posts', 'can_manage_users', 'can_manage_payments', 
                      'can_view_analytics', 'can_manage_config')
        }),
    )
    
    def full_name(self, obj):
        if obj.first_name and obj.last_name:
            return f"{obj.first_name} {obj.last_name}"
        return obj.first_name or obj.username or "Без имени"
    full_name.short_description = 'Полное имя'
    
    def permissions_summary(self, obj):
        permissions = []
        if obj.can_moderate_posts:
            permissions.append('Модерация')
        if obj.can_manage_users:
            permissions.append('Пользователи')
        if obj.can_manage_payments:
            permissions.append('Платежи')
        if obj.can_view_analytics:
            permissions.append('Аналитика')
        if obj.can_manage_config:
            permissions.append('Конфигурация')
        
        if not permissions:
            return format_html('<span style="color: #999;">Нет прав</span>')
        
        return ', '.join(permissions)
    permissions_summary.short_description = 'Права'


@admin.register(SystemLog)
class SystemLogAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'level', 'message_short', 'module', 'user_id')
    list_filter = ('level', 'module', 'created_at')
    search_fields = ('message', 'module', 'user_id')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
    
    def message_short(self, obj):
        return obj.message[:100] + '...' if len(obj.message) > 100 else obj.message
    message_short.short_description = 'Сообщение'
    
    def has_add_permission(self, request):
        # Логи создаются только программно
        return False
    
    def has_change_permission(self, request, obj=None):
        # Логи нельзя изменять
        return False
    
    actions = ['delete_selected']
    
    def get_actions(self, request):
        actions = super().get_actions(request)
        # Оставляем только удаление для очистки старых логов
        return {'delete_selected': actions['delete_selected']} if 'delete_selected' in actions else {}
