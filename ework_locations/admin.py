from django.contrib import admin
from django.utils.html import format_html
from .models import City


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ('name', 'users_count', 'posts_count', 'order')
    search_fields = ('name',)
    ordering = ('order', 'name')
    
    def users_count(self, obj):
        count = obj.telegramuser_set.filter(is_active=True).count()
        return format_html('<strong>{}</strong>', count)
    users_count.short_description = 'Пользователей'
    
    def posts_count(self, obj):
        from ework_job.models import PostJob
        from ework_services.models import PostServices
        
        jobs_count = PostJob.objects.filter(city=obj).count()
        services_count = PostServices.objects.filter(city=obj).count()
        total = jobs_count + services_count
        
        return format_html('<strong>{}</strong> (работа: {}, услуги: {})', total, jobs_count, services_count)
    posts_count.short_description = 'Объявлений'