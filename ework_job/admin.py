from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import PostJob
from ework_rubric.models import SuperRubric
from django.utils.translation import gettext_lazy as _


class SubRubricListFilter(admin.SimpleListFilter):
    """Пользовательский фильтр для подрубрик услуг"""
    title = _('Подрубрика')
    parameter_name = 'sub_rubric'

    def lookups(self, request, model_admin):
        """Возвращает список кортежей (значение, отображаемое название)"""
        result = []
        
        # Получаем родительскую рубрику "Рбота"
        job_rubric = SuperRubric.objects.filter(slug='rabota').first()
        
        if job_rubric:            
            # Добавляем подрубрики этой родительской рубрики
            for sub_rubric in job_rubric.sub_rubrics.all().order_by('order'):
                result.append((str(sub_rubric.id), f'    {sub_rubric.name}'))
                
        return result

    def queryset(self, request, queryset):
        """Фильтрует queryset на основе выбранного значения"""
        # Если выбрана подрубрика
        if self.value() and not self.value().startswith('category_'):
            return queryset.filter(sub_rubric_id=self.value())
        return queryset


@admin.register(PostJob)
class PostJobAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'city', 'price_display', 'status', 'is_premium', 'image_preview', 'created_at')
    list_filter = ('status', 'city', SubRubricListFilter, 'created_at')
    search_fields = ('title', 'description', 'user__username', 'user__first_name', 'user__last_name')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'description', 'user', 'city', 'sub_rubric')
        }),
        ('Цена и условия', {
            'fields': ('price', 'currency')
        }),
        ('Параметры работы', {
            'fields': ('experience', 'work_schedule', 'work_format')
        }),
        ('Дополнительные условия', {
            'fields': ('status', 'is_premium'),
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
        return _("Не указана")
    price_display.short_description = _('Цена')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'city', 'currency', 'sub_rubric')
    
    actions = ['make_premium', 'make_regular', 'approve_posts', 'reject_posts', 'archive_posts']

    def image_preview(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" style="max-height: 50px; max-width: 50px;">')
        return _("Нет изображения")
    image_preview.short_description = _('Изображение')
        
    def approve_posts(self, request, queryset):
        """Одобрить посты (ручная модерация)"""
        updated = queryset.filter(status=1).update(status=3) 
        self.message_user(request, f"Одобрено: {updated} объявлений")
    approve_posts.short_description = _("Одобрить посты")
    
    def reject_posts(self, request, queryset):
        """Отклонить посты (ручная модерация)"""
        updated = queryset.exclude(status=2).update(status=2) 
        self.message_user(request, f"Отклонено: {updated} объявлений")
    reject_posts.short_description = _("Отклонить посты")
    
    def archive_posts(self, request, queryset):
        """Архивировать посты"""
        updated = queryset.update(status=4)
        self.message_user(request, f"Архивировано: {updated} объявлений")
    archive_posts.short_description = _("Архивировать")
