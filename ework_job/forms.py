
from django import forms
from ework_post.forms import BasePostForm
from ework_job.models import PostJob

class JobPostForm(BasePostForm):
    class Meta(BasePostForm.Meta):
        model = PostJob
        fields = BasePostForm.Meta.fields + [ 'experience', 'work_schedule', 'type_of_work', 'work_format' ]
        widgets = {
            'experience': forms.Select(attrs={'class': 'form-control'}),
            'work_schedule': forms.Select(attrs={'class': 'form-control'}),
            'type_of_work': forms.Select(attrs={'class': 'form-control'}),
            'work_format': forms.Select(attrs={'class': 'form-control'}),
        }