from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from ework_post.models import AbsPost
from ework_locations.models import City
from ework_currency.models import Currency
from ework_premium.models import Package
from ework_premium.utils import PricingCalculator

from ework_rubric.models import SubRubric


class BasePostForm(forms.ModelForm):
    # Поля для аддонов
    addon_photo = forms.BooleanField(
        required=False,
        label=_('Добавить фото'),
        help_text=_('Разрешить добавление фото к объявлению (+30 дней)')
    )
    addon_highlight = forms.BooleanField(
        required=False,
        label=_('Выделить цветом'),
        help_text=_('Выделить объявление цветным фоном (+3 дня)')
    )
    addon_auto_bump = forms.BooleanField(
        required=False,
        label=_('Автоподнятие'),
        help_text=_('Автоматически поднимать объявление каждые 12 часов (+7 дней)')
    )
    
    class Meta:
        model = AbsPost
        fields = ['title', 'description', 'image', 'city', 'price', 'currency', 'sub_rubric', 'user_phone' ]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super().__init__(*args, **kwargs)
        
        # Инициализируем калькулятор цен
        self.pricing_calculator = PricingCalculator(self.user)
        # Оптимизированные queryset
        currency_qs = Currency.objects.order_by('order')
        self.fields['currency'].queryset = currency_qs
        self.fields['currency'].empty_label = None
        first = currency_qs.first()
        if first is not None:
            self.fields['currency'].initial = first.pk

        city_qs = City.objects.order_by('order')
        self.fields['city'].queryset = city_qs
        self.fields['city'].empty_label = None
        first = city_qs.first()
        if first is not None:
            self.fields['city'].initial = first.pk
        
        sub_rubric_qs = SubRubric.objects.select_related('super_rubric').order_by(
            'super_rubric__order', 'order'
        )
        self.fields['sub_rubric'].queryset = sub_rubric_qs
        self.fields['sub_rubric'].empty_label = None
        first = sub_rubric_qs.first()
        if first is not None:
            self.fields['sub_rubric'].initial = first.pk

        if 'user_phone' in self.fields and self.user:
            if hasattr(self.user, 'phone') and self.user.phone:
                self.fields['user_phone'].initial = self.user.phone
                
        # Настройка видимости поля image в зависимости от аддона фото
        self._setup_image_field()
    
    def _setup_image_field(self):
        """Настроить поле изображения"""
        # При первом рендере формы (когда data пустая) оставляем поле как есть
        # JS сам покажет/скроет его в зависимости от аддона
        if self.data:  # Только если форма уже была отправлена
            if not self.data.get('addon_photo'):
                self.fields['image'].widget = forms.HiddenInput()
                self.fields['image'].required = False
            else:
                # Возвращаем обычный FileInput если аддон выбран
                self.fields['image'].widget = forms.FileInput(attrs={'class': 'form-control'})
                self.fields['image'].required = False
    
    def get_pricing_breakdown(self):
        """Получить разбивку цен"""
        return self.pricing_calculator.get_pricing_breakdown(
            photo=self.data.get('addon_photo', False),
            highlight=self.data.get('addon_highlight', False),
            auto_bump=self.data.get('addon_auto_bump', False)
        )
    
    def get_button_config(self):
        """Получить конфигурацию кнопки"""
        return self.pricing_calculator.get_button_config(
            photo=self.data.get('addon_photo', False),
            highlight=self.data.get('addon_highlight', False),
            auto_bump=self.data.get('addon_auto_bump', False)
        )
    
    def clean(self):
        """Валидация формы"""
        cleaned_data = super().clean()
        
        # Если выбран аддон фото, изображение обязательно
        if cleaned_data.get('addon_photo') and not cleaned_data.get('image'):
            raise ValidationError({
                'image': _('Изображение обязательно при выборе аддона "Фото"')
            })
        
        return cleaned_data