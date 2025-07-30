from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import BannerPost


@admin.register(BannerPost)
class BannerPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'image_preview', 'link', 'is_active', 'order', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('title', 'description')
    list_editable = ('is_active', 'order')
    ordering = ('order', '-created_at')
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'description', 'link')
        }),
        ('Изображение', {
            'fields': ('image', 'image_preview'),
        }),
        ('Настройки', {
            'fields': ('is_active', 'order')
        }),
        ('Системная информация', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'image_preview')
    
    def image_preview(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" style="max-height: 50px; max-width: 50px;">')
        return "Нет изображения"
    image_preview.short_description = 'Превью'
    
    actions = ['activate', 'deactivate']
    
    def activate(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f"Активировано: {queryset.count()} баннеров")
    activate.short_description = "Активировать"
    
    def deactivate(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f"Деактивировано: {queryset.count()} баннеров")
    deactivate.short_description = "Деактивировать"