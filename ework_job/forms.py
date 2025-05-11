
from django import forms
from ework_post.forms import BasePostForm
from ework_job.models import PostJob
from ework_rubric.models import Rubric, SubRubric, SuperRubric

class JobPostForm(BasePostForm):
    class Meta(BasePostForm.Meta):
        model = PostJob
        fields = BasePostForm.Meta.fields + [ 'experience', 'work_schedule', 'type_of_work', 'work_format' ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            vacancy_rubric = Rubric.objects.get(slug='rabota')

        except Rubric.DoesNotExist:
            vacancy_rubric = None

        if vacancy_rubric:
            qs = SubRubric.objects.filter(
                super_rubric=vacancy_rubric
            ).order_by('order')
        else:
            qs = SubRubric.objects.none()

        self.fields['sub_rubric'].queryset = qs
        self.fields['sub_rubric'].empty_label = None

        first = qs.first()
        if first:
            self.fields['sub_rubric'].initial = first.pk