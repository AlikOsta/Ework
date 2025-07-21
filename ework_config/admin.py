from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.http import HttpResponseRedirect
from .models import SiteConfig


@admin.register(SiteConfig)
class SiteConfigAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Основные настройки сайта', {
            'fields': ('site_name', 'site_url'),
            'classes': ('collapse',)
        }),
        ('Telegram Bot', {
            'fields': ('bot_token', 'bot_username'),
            'classes': ('collapse',)
        }),
        ('Уведомления', {
            'fields': ('notification_bot_token', 'admin_chat_id', 'admin_username'),
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
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def has_add_permission(self, request):
        return not SiteConfig.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def changelist_view(self, request, extra_context=None):
        try:
            config = SiteConfig.objects.get(pk=1)
            return HttpResponseRedirect(reverse('admin:ework_config_siteconfig_change', args=[config.pk]))
        except SiteConfig.DoesNotExist:
            return super().changelist_view(request, extra_context)


