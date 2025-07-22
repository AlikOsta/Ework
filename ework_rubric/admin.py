from django.contrib import admin
from django.utils.html import format_html
from .models import SuperRubric, SubRubric
from .forms import SubRubricForm


@admin.register(SuperRubric)
class SuperRubricAdmin(admin.ModelAdmin):
    list_display = ('name', 'sub_rubrics_count', 'order')
    search_fields = ('name',)
    ordering = ('order', 'name')
    
    def sub_rubrics_count(self, obj):
        count = obj.sub_rubrics.count()
        return format_html('<strong>{}</strong>', count)
    sub_rubrics_count.short_description = 'Подрубрик'


@admin.register(SubRubric)
class SubRubricAdmin(admin.ModelAdmin):
    list_display = ('name', 'super_rubric', 'posts_count', 'order')
    list_filter = ('super_rubric',)
    search_fields = ('name', 'super_rubric__name')
    ordering = ('super_rubric__order', 'order', 'name')
    form = SubRubricForm
    
    def posts_count(self, obj):
        from ework_job.models import PostJob
        from ework_services.models import PostServices
        
        jobs_count = PostJob.objects.filter(sub_rubric=obj).count()
        services_count = PostServices.objects.filter(sub_rubric=obj).count()
        total = jobs_count + services_count
        
        return format_html('<strong>{}</strong> (работа: {}, услуги: {})', total, jobs_count, services_count)
    posts_count.short_description = 'Объявлений'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('super_rubric')
