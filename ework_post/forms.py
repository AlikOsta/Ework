from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from ework_post.models import AbsPost
from ework_locations.models import City
from ework_currency.models import Currency
from ework_premium.models import Package, FreePostRecord
from ework_rubric.models import SubRubric


class BasePostForm(forms.ModelForm):
    package = forms.ModelChoiceField(
        queryset=Package.objects.filter(is_active=True).order_by('order'),
        widget=forms.RadioSelect,
        label=_("Тариф"),
        help_text=_("Выберите тариф для публикации")
    )
    
    class Meta:
        model = AbsPost
        fields = ['title', 'description', 'image', 'city', 'price', 'currency', 'sub_rubric', 'user_phone', 'package']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super().__init__(*args, **kwargs)
        
        # Настройка валют
        self.fields['currency'].queryset = Currency.objects.all().order_by('order')
        self.fields['currency'].empty_label = None
        first = self.fields['currency'].queryset.first()
        if first is not None:
            self.fields['currency'].initial = first.pk

        # Настройка городов
        self.fields['city'].queryset = City.objects.all().order_by('order')
        self.fields['city'].empty_label = None
        first = self.fields['city'].queryset.first()
        if first is not None:
            self.fields['city'].initial = first.pk
        
        # Настройка подрубрик
        self.fields['sub_rubric'].queryset = SubRubric.objects.all().order_by('order')
        self.fields['sub_rubric'].empty_label = None
        first = self.fields['sub_rubric'].queryset.first()
        if first is not None:
            self.fields['sub_rubric'].initial = first.pk

        # Настройка телефона пользователя
        if 'user_phone' in self.fields and self.user:
            if hasattr(self.user, 'phone') and self.user.phone:
                self.fields['user_phone'].initial = self.user.phone

        # Настройка тарифов
        self.setup_package_field()
        
        # Добавляем CSS классы и атрибуты
        self.setup_field_attributes()

    def setup_package_field(self):
        """Настройка поля выбора тарифа"""
        packages = Package.objects.filter(is_active=True).order_by('order')
        
        # Проверяем, может ли пользователь использовать бесплатный тариф
        can_use_free = FreePostRecord.can_user_post_free(self.user)
        
        if can_use_free:
            # Если можно использовать бесплатный, выбираем его по умолчанию
            free_package = packages.filter(package_type='FREE_WEEKLY').first()
            if free_package:
                self.fields['package'].initial = free_package.pk
        else:
            # Если нет, выбираем первый платный
            paid_package = packages.filter(package_type='PAID').first()
            if paid_package:
                self.fields['package'].initial = paid_package.pk

        # Добавляем информацию о доступности бесплатного тарифа
        self.can_use_free_package = can_use_free

    def setup_field_attributes(self):
        """Настройка атрибутов полей формы"""
        # Добавляем CSS классы
        css_classes = {
            'title': 'form-control',
            'description': 'form-control',
            'price': 'form-control',
            'user_phone': 'form-control',
            'city': 'form-select',
            'currency': 'form-select',
            'sub_rubric': 'form-select',
            'image': 'form-control',
        }
        
        for field_name, css_class in css_classes.items():
            if field_name in self.fields:
                self.fields[field_name].widget.attrs.update({'class': css_class})

        # Специальные атрибуты для поля изображения
        if 'image' in self.fields:
            self.fields['image'].widget.attrs.update({
                'accept': 'image/*',
                'id': 'id_image'
            })

    def clean(self):
        cleaned_data = super().clean()
        package = cleaned_data.get('package')
        image = cleaned_data.get('image')
        
        # Проверяем логику тарифов и изображений
        if package:
            # Если выбран тариф без фото, но загружено изображение
            if not package.allows_photo and image:
                raise ValidationError(_('Выбранный тариф не поддерживает добавление фотографий'))
            
            # Если выбран бесплатный тариф, но пользователь уже использовал его
            if package.is_free() and not FreePostRecord.can_user_post_free(self.user):
                raise ValidationError(_('Вы уже использовали бесплатную публикацию на этой неделе'))

        return cleaned_data

    def get_package_info(self):
        """Получить информацию о доступных тарифах для шаблона"""
        packages = Package.objects.filter(is_active=True).order_by('order')
        package_info = []
        
        for package in packages:
            info = {
                'id': package.id,
                'name': package.name,
                'description': package.description,
                'price': package.price_per_post,
                'currency': package.currency.code if package.currency else '',
                'allows_photo': package.allows_photo,
                'is_free': package.is_free(),
                'icon_flag': package.icon_flag,
                'highlight_color': package.highlight_color,
            }
            
            # Для бесплатного тарифа проверяем доступность
            if package.is_free():
                info['available'] = FreePostRecord.can_user_post_free(self.user)
                if not info['available']:
                    info['disabled_reason'] = _('Бесплатная публикация уже использована на этой неделе')
            else:
                info['available'] = True
                
            package_info.append(info)
        
        return package_info