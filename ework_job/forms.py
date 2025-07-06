
from django import forms
from ework_post.forms import BasePostForm
from ework_job.models import PostJob
from ework_rubric.models import SubRubric, SuperRubric

class JobPostForm(BasePostForm):
    class Meta(BasePostForm.Meta):
        model = PostJob
        fields = BasePostForm.Meta.fields + [ 'experience', 'work_schedule', 'work_format']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            job_rubric = SuperRubric.objects.get(slug='rabota')
            qs = SubRubric.objects.filter(super_rubric=job_rubric).order_by('order')
        except SuperRubric.DoesNotExist:
            qs = SubRubric.objects.none()

        self.fields['sub_rubric'].queryset = qs
        self.fields['sub_rubric'].empty_label = None

        first = qs.first()
        if first:
            self.fields['sub_rubric'].initial = first.pk

    def _copy_from_post(self, post_id):
        """Копирование данных из существующего поста вакансии"""
        try:
            from ework_job.models import PostJob
            
            # Получаем пост-вакансию для копирования
            source_post = PostJob.objects.get(
                id=post_id,
                user=self.user,
                status__in=[4]  # Только архивные
            )
            
            # Вызываем базовое копирование
            super()._copy_from_post(post_id)
            
            # Копируем специфичные для вакансии поля
            self.fields['experience'].initial = source_post.experience
            self.fields['work_schedule'].initial = source_post.work_schedule
            self.fields['work_format'].initial = source_post.work_format
            
        except PostJob.DoesNotExist:
            # Если это не пост-вакансия, пробуем базовое копирование
            super()._copy_from_post(post_id)
