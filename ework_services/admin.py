from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import PostServices


@admin.register(PostServices)
class PostServicesAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'city', 'price_display', 'status', 'is_premium', 'image_preview', 'created_at')
    list_filter = ('status', 'city', 'sub_rubric', 'created_at')
    search_fields = ('title', 'description', 'user__username', 'user__first_name', 'user__last_name')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'description', 'user', 'city', 'sub_rubric')
        }),
        ('Цена и условия', {
            'fields': ('price', 'currency')
        }),
        ('Статус и настройки', {
            'fields': ('status', 'is_premium')
        }),
        ('Изображения', {
            'fields': ('image',),
            'classes': ('collapse',)
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def price_display(self, obj):
        if obj.price and obj.currency:
            return f"{obj.price} {obj.currency.symbol}"
        return "Не указана"
    price_display.short_description = 'Цена'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'city', 'currency', 'sub_rubric')
    
    actions = ['make_premium', 'make_regular', 'approve_posts', 'reject_posts', 'archive_posts']
    
    def make_premium(self, request, queryset):
        queryset.update(is_premium=True)
        self.message_user(request, f"Сделано премиум: {queryset.count()} объявлений")
    make_premium.short_description = "Сделать премиум"
    
    def make_regular(self, request, queryset):
        queryset.update(is_premium=False)
        self.message_user(request, f"Убрано премиум: {queryset.count()} объявлений")
    make_regular.short_description = "Убрать премиум"
    
    def approve_posts(self, request, queryset):
        """Одобрить посты (ручная модерация)"""
        updated = queryset.filter(status=1).update(status=3)  # На модерации → Опубликовано
        self.message_user(request, f"Одобрено: {updated} объявлений")
    approve_posts.short_description = "Одобрить посты"
    
    def reject_posts(self, request, queryset):
        """Отклонить посты (ручная модерация)"""
        updated = queryset.exclude(status=2).update(status=2)  # → Отклонено
        self.message_user(request, f"Отклонено: {updated} объявлений")
    reject_posts.short_description = "Отклонить посты"
    
    def archive_posts(self, request, queryset):
        """Архивировать посты"""
        updated = queryset.update(status=4)  # → Архив
        self.message_user(request, f"Архивировано: {updated} объявлений")
    archive_posts.short_description = "Архивировать"

    def image_preview(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" style="max-height: 50px; max-width: 50px;">')
        return "Нет изображения"
    image_preview.short_description = 'Превью'
