from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from ework_post.models import AbsPost
from ework_locations.models import City
from ework_currency.models import Currency

from ework_rubric.models import SubRubric


class BasePostForm(forms.ModelForm):
    """
    Базовая форма для создания и редактирования объявлений.
    Наследуется конкретными формами в приложениях.
    """

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        self.fields['title'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': _('Введите название объявления')
        })

        self.fields['sub_rubric'].queryset = SubRubric.objects.all().order_by('order', 'name')
        self.fields['sub_rubric'].widget.attrs.update({
            'class': 'form-select'
        })
        
        self.fields['description'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': _('Подробно опишите ваше объявление'),
            'rows': 5
        })

        self.fields['sub_rubric'].queryset = SubRubric.objects.all().order_by('order', 'name')
        self.fields['sub_rubric'].widget.attrs.update({
            'class': 'form-select'
        })

        self.fields['price'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': _('Укажите сумму')
        })
        
        self.fields['city'].queryset = City.objects.all().order_by('order', 'name')
        self.fields['city'].widget.attrs.update({
            'class': 'form-select'
        })
        
        self.fields['currency'].queryset = Currency.objects.all().order_by('order')
        self.fields['currency'].widget.attrs.update({
            'class': 'form-select'
        })
        
        self.fields['image'].widget.attrs.update({
            'class': 'form-control',
            'accept': 'image/*'
        })
        
        if self.user and self.user.phone:
            self.initial['user_phone'] = self.user.phone
    
    def clean_title(self):
        """Валидация заголовка объявления"""
        title = self.cleaned_data.get('title')
        if len(title) < 5:
            raise ValidationError(_('Заголовок должен содержать не менее 5 символов'))
        return title
    
    def clean_description(self):
        """Валидация описания объявления"""
        description = self.cleaned_data.get('description')
        if len(description) < 20:
            raise ValidationError(_('Описание должно содержать не менее 20 символов'))
        return description
    
    def clean_price(self):
        """Валидация цены"""
        price = self.cleaned_data.get('price')
        if price <= 0:
            raise ValidationError(_('Сумма должна быть положительным числом'))
        return price
    
    def clean_image(self):
        """Валидация изображения"""
        image = self.cleaned_data.get('image')
        if image:
            if image.size > 5 * 1024 * 1024:
                raise ValidationError(_('Размер изображения не должен превышать 5 МБ'))
            
            allowed_extensions = ['jpg', 'jpeg', 'png', 'gif']
            ext = image.name.split('.')[-1].lower()
            if ext not in allowed_extensions:
                raise ValidationError(_('Поддерживаемые форматы изображений: JPG, JPEG, PNG, GIF'))
        
        return image
    
    class Meta:
        model = AbsPost
        fields = ['title', 'description', 'image', 'city', 'price', 'currency', 'sub_rubric']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'city': forms.Select(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'currency': forms.Select(attrs={'class': 'form-control'}),
            'sub_rubric': forms.Select(attrs={'class': 'form-control'}),
        }