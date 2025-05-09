
from django import forms
from .models import SuperRubric, SubRubric
from django.utils.translation import gettext_lazy as _


class SubRubricForm(forms.ModelForm):
    super_rubric = forms.ModelChoiceField(
        queryset=SuperRubric.objects.all(),
        empty_label=None,
        label=_("Родительская рубрика"),
        required=True
    )

    class Meta:
        model = SubRubric
        fields = '__all__'