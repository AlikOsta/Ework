from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from ework_post.models import AbsPost
from ework_locations.models import City
from ework_currency.models import Currency

from ework_rubric.models import SubRubric


class BasePostForm(forms.ModelForm):
    class Meta:
        model = AbsPost
        fields = ['title', 'description', 'image', 'city', 'price', 'currency', 'sub_rubric', 'user_phone' ]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super().__init__(*args, **kwargs)
        self.fields['currency'].queryset = Currency.objects.all().order_by('order')
        self.fields['currency'].empty_label = None
        first =self.fields['currency'].queryset.first()
        if first is not None:
            self.fields['currency'].initial = first.pk

        self.fields['city'].queryset = City.objects.all().order_by('order')
        self.fields['city'].empty_label = None
        first = self.fields['city'].queryset.first()
        if first is not None:
            self.fields['city'].initial = first.pk
        
        self.fields['sub_rubric'].queryset = SubRubric.objects.all().order_by('order')
        self.fields['sub_rubric'].empty_label = None
        first = self.fields['sub_rubric'].queryset.first()
        if first is not None:
            self.fields['sub_rubric'].initial = first.pk

        # Проверяем, есть ли поле user_phone в форме
        if 'user_phone' in self.fields and self.user:
            # Проверяем, есть ли у пользователя телефон напрямую
            if hasattr(self.user, 'phone') and self.user.phone:
                self.fields['user_phone'].initial = self.user.phone