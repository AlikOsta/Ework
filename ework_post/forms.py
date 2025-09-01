from django import forms
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

from ework_post.models import AbsPost
from ework_rubric.models import SubRubric
from ework_locations.models import City
from ework_currency.models import Currency
from ework_rubric.models import SuperRubric


class BasePostForm(forms.ModelForm):
    """Оптимизированная базовая форма для создания постов"""
    
    addon_photo = forms.BooleanField(
        required=False,
        label=_('Добавить фото'),
        help_text=_('Возможность добавлять фото к объявлению')
    )
    addon_highlight = forms.BooleanField(
        required=False,
        label=_('Выделить цветом'),
        help_text=_('Объявление будет выделено цветом')
    )

    class Meta:
        model = AbsPost
        fields = [
            'title', 'description', 'image', 'price', 'currency',
            'sub_rubric', 'city', 'user_phone', 'address'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Введите название объявления'),
                'maxlength': '50'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': _('Опишите ваше объявление')
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': _('Укажите цену')
            }),
            'currency': forms.Select(attrs={'class': 'form-select'}),
            'sub_rubric': forms.Select(attrs={'class': 'form-select'}),
            'city': forms.Select(attrs={'class': 'form-select'}),
            'user_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Ваш номер телефона')
            }),
            'address': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Введите адрес'),
                'maxlength': '50'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['currency'].queryset = Currency.objects.all()
        self.fields['city'].queryset = City.objects.order_by('order', 'name')
        self.fields['sub_rubric'].queryset = SubRubric.objects.select_related('super_rubric').order_by('order')
        if self.user and hasattr(self.user, 'phone') and self.user.phone:
            self.fields['user_phone'].initial = self.user.phone
        default_currency = Currency.objects.first()
        if default_currency:
            self.fields['currency'].initial = default_currency.pk

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price is not None and price < 0:
            raise forms.ValidationError(_('Цена не может быть отрицательной'))
        return price

    def clean_title(self):
        title = self.cleaned_data.get('title', '').strip()
        if len(title) < 5:
            raise forms.ValidationError(_('Название должно содержать минимум 5 символов'))
        return title

    def clean_description(self):
        description = self.cleaned_data.get('description', '').strip()
        if len(description) < 10:
            raise forms.ValidationError(_('Описание должно содержать минимум 10 символов'))
        return description

    def _set_subrubric_queryset(self, super_rubric_slug):
        try:
            super_rubric = SuperRubric.objects.get(slug=super_rubric_slug)
            qs = SubRubric.objects.filter(super_rubric=super_rubric).order_by('order')
        except SuperRubric.DoesNotExist:
            qs = SubRubric.objects.none()

        self.fields['sub_rubric'].queryset = qs
        self.fields['sub_rubric'].empty_label = None

        first = qs.first()
        if first:
            self.fields['sub_rubric'].initial = first.pk