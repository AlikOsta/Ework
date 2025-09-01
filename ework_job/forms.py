from django import forms
from ework_post.forms import BasePostForm
from ework_job.models import PostJob
from ework_rubric.models import SubRubric, SuperRubric

class JobPostForm(BasePostForm):
    class Meta(BasePostForm.Meta):
        model = PostJob
        fields = BasePostForm.Meta.fields + ['experience', 'work_schedule']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._set_subrubric_queryset(super_rubric_slug='rabota')