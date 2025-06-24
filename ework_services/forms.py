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
        try:
            services_rubric = SuperRubric.objects.get(slug='uslugi')
            qs = SubRubric.objects.filter(super_rubric=services_rubric).order_by('order')
        except SuperRubric.DoesNotExist:
            qs = SubRubric.objects.none()

        self.fields['sub_rubric'].queryset = qs
        self.fields['sub_rubric'].empty_label = None

        first = qs.first()
        if first:
            self.fields['sub_rubric'].initial = first.pk