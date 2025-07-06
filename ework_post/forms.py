from django import forms
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

from ework_post.models import AbsPost
from ework_rubric.models import SubRubric
from ework_locations.models import City
from ework_currency.models import Currency


class BasePostForm(forms.ModelForm):
    """базовая форма для создания постов"""
    
    addon_photo = forms.BooleanField(
        required=False,
        label=_('Добавить фото'),
        help_text=_('Возможность добавлять фото к объявлению')
    )
    addon_highlight = forms.BooleanField(
        required=False,
        label=_('Выделить цветом'),
        help_text=_('Объявление будет выделено цветом для привлечения внимания')
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
                'placeholder': _('Введите адресс'),
                'maxlength': '50'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.copy_from_id = kwargs.pop('copy_from', None)
        self.is_create = kwargs.pop('is_create', True) 
        
        super().__init__(*args, **kwargs)
        
        self.fields['currency'].queryset = Currency.objects.all()
        self.fields['city'].queryset = City.objects.order_by('order', 'name')
        self.fields['sub_rubric'].queryset = SubRubric.objects.select_related('super_rubric').order_by('order')
        
        if self.user and hasattr(self.user, 'phone') and self.user.phone:
            self.fields['user_phone'].initial = self.user.phone
        
        default_currency = Currency.objects.first()
        if default_currency:
            self.fields['currency'].initial = default_currency.pk

        if self.copy_from_id:
            self._copy_from_post(self.copy_from_id)
            
        if self.is_create:
            self.fields['addon_photo'] = forms.BooleanField(
                required=False,
                label=_('Добавить фото'),
                help_text=_('Возможность добавлять фото к объявлению')
            )
            self.fields['addon_highlight'] = forms.BooleanField(
                required=False,
                label=_('Выделить цветом'),
                help_text=_('Объявление будет выделено цветом для привлечения внимания')
            )

    def clean(self):
        """Дополнительная валидация формы"""
        cleaned_data = super().clean()
    
        if not self.is_create:
            addon_fields = ['addon_photo', 'addon_highlight', 'addon_auto_bump']
            for field in addon_fields:
                if field in cleaned_data:
                    del cleaned_data[field]
                    
        return cleaned_data
        
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

    def _copy_from_post(self, post_id):
        """Копирование данных из существующего поста"""
        try:
            from ework_post.models import AbsPost
            
            source_post = AbsPost.objects.get(
                id=post_id,
                user=self.user,
                status__in=[4]  
            )
            
            self.fields['title'].initial = source_post.title
            self.fields['description'].initial = source_post.description
            self.fields['price'].initial = source_post.price
            self.fields['currency'].initial = source_post.currency_id
            self.fields['sub_rubric'].initial = source_post.sub_rubric_id
            self.fields['city'].initial = source_post.city_id
            self.fields['user_phone'].initial = source_post.user_phone
            self.fields['address'].initial = source_post.address
            
            self._copied_from_title = source_post.title
            
        except AbsPost.DoesNotExist:
            pass
    
    def get_copied_from_title(self):
        """Получить название скопированного поста для отображения"""
        return getattr(self, '_copied_from_title', None)
    
    def is_edit_mode(self):
        """Проверяет, находится ли форма в режиме редактирования"""
        return self.instance and self.instance.pk is not None