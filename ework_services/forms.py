from django import forms
from ework_post.forms import BasePostForm
from ework_services.models import PostServices
from ework_rubric.models import SubRubric, SuperRubric

class ServicesPostForm(BasePostForm):
    class Meta(BasePostForm.Meta):
        model = PostServices
        fields = BasePostForm.Meta.fields

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._set_subrubric_queryset(super_rubric_slug='uslugi')