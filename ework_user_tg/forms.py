from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from ework_locations.models import City

User = get_user_model()

class UserProfileForm(forms.ModelForm):
    """Форма для редактирования профиля пользователя"""
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'city', 'phone']
        labels = {
            'first_name': _('Имя'),
            'last_name': _('Фамилия'),
            'city': _('Город'),
            'phone': _('Телефон'),
        }
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': _('Введите ваше имя')
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': _('Введите вашу фамилию')
            }),
            'city': forms.Select(attrs={
                'class': 'form-select'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Введите номер телефона'),
                'type': 'tel'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['city'].queryset = City.objects.all()
        self.fields['city'].empty_label = _("Выберите город")
        
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone:
            # Простая валидация номера телефона
            import re
            if not re.match(r'^\+?[\d\s\-\(\)]{10,15}$', phone):
                raise forms.ValidationError(_('Введите корректный номер телефона'))
        return phone
