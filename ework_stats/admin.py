from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from .models import DailyStats

@admin.register(DailyStats)
class DailyStatsAdmin(admin.ModelAdmin):
    list_display = ('date', 'new_users', 'new_posts', 'post_views', 'favorites_added')
    list_filter = ('date',)
    ordering = ('-date',)
    readonly_fields = ('date', 'new_users', 'new_posts', 'post_views', 'favorites_added')
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['stats_links'] = [
            {
                'title': 'Общая статистика',
                'url': reverse('ework_stats:dashboard_stats'),
                'icon': '📊'
            },
            {
                'title': 'Статистика пользователей',
                'url': reverse('ework_stats:user_stats'),
                'icon': '👥'
            },
            {
                'title': 'Статистика объявлений',
                'url': reverse('ework_stats:post_stats'),
                'icon': '📝'
            },
            {
                'title': 'Статистика просмотров',
                'url': reverse('ework_stats:views_stats'),
                'icon': '👁️'
            }
        ]
        return super().changelist_view(request, extra_context)
