
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
