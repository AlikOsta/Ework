from django.contrib import admin
from django.utils.html import format_html
from .models import TelegramUser
from ework_post.models import PostView


@admin.register(TelegramUser)
class TelegramUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'full_name', 'telegram_id', 'city', 'rating_display', 'is_active', 'created_at')
    def full_name(self, obj):
        if obj.first_name and obj.last_name:
            return f"{obj.first_name} {obj.last_name}"
        return obj.first_name or "Без имени"
    full_name.short_description = 'Полное имя'
    
    def rating_display(self, obj):
        avg_rating = getattr(obj, 'average_rating', 0)
        ratings_count = getattr(obj, 'ratings_count', 0)
        
        if avg_rating > 0:
            stars = '★' * int(avg_rating) + '☆' * (5 - int(avg_rating))
            return format_html(
                '<span style="color: #ffa500;">{}</span> ({}/5, {} отзывов)',
                stars, round(avg_rating, 1), ratings_count
            )
        return format_html('<span style="color: #999;">Нет отзывов</span>')
    rating_display.short_description = 'Рейтинг'
