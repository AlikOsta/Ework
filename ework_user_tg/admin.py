from django.contrib import admin
from django.utils.html import format_html
from .models import TelegramUser
from ework_post.models import PostView


@admin.register(TelegramUser)
class TelegramUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'full_name', 'telegram_id', 'city', 'rating_display', 'balance', 'is_active', 'created_at')
    list_filter = ('is_active', 'is_staff', 'language', 'city', 'created_at')
    search_fields = ('username', 'telegram_id', 'first_name', 'last_name', 'email', 'phone')
    readonly_fields = ('telegram_id', 'created_at', 'updated_at', 'last_login', 'date_joined', 'rating_display')
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('username', 'email', 'telegram_id', 'first_name', 'last_name', 'phone')
        }),
        ('Персональные данные', {
            'fields': ('photo_url', 'language', 'city', 'balance'),
        }),
        ('Рейтинг', {
            'fields': ('rating_display',),
        }),
        ('Права доступа', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        ('Временные метки', {
            'fields': ('last_login', 'date_joined', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def full_name(self, obj):
        if obj.first_name and obj.last_name:
            return f"{obj.first_name} {obj.last_name}"
        return obj.first_name or "Без имени"
    full_name.short_description = 'Полное имя'
    
    def rating_display(self, obj):
        avg_rating = obj.average_rating
        ratings_count = obj.ratings_count
        
        if avg_rating > 0:
            stars = '★' * int(avg_rating) + '☆' * (5 - int(avg_rating))
            return format_html(
                '<span style="color: #ffa500;">{}</span> ({:.1f}/5, {} отзывов)',
                stars, avg_rating, ratings_count
            )
        return format_html('<span style="color: #999;">Нет отзывов</span>')
    rating_display.short_description = 'Рейтинг'


