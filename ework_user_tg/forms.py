from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.conf import settings

User = get_user_model()

class UserProfileForm(forms.ModelForm):

    language = forms.ChoiceField(
        choices=settings.LANGUAGES,
        label=_('Язык интерфейса'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'city', 'phone', 'language']
        labels = {
            'first_name': _('Имя'),
            'last_name': _('Фамилия'),
            'city': _('Город'),
            'phone': _('Телефон'),
        }
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if self.instance and hasattr(self.instance, 'language'):
            self.fields['language'].initial = self.instance.language

        if 'city' in self.fields:
            from ework_locations.models import City
            self.fields['city'].queryset = City.objects.all()
            self.fields['city'].widget.attrs.update({'class': 'form-control'})


class UserRatingForm(forms.ModelForm):
    """Форма для оставления отзыва пользователю"""
    
    rating = forms.ChoiceField(
        choices=[(i, f"{i} ⭐") for i in range(1, 6)],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label=_('Оценка'),
        help_text=_('Выберите оценку от 1 до 5 звезд')
    )
    
    comment = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control', 
            'rows': 3, 
            'placeholder': _('Напишите отзыв (необязательно)')
        }),
        label=_('Комментарий'),
        required=False,
        max_length=550
    )
    
    class Meta:
        from .models import UserRating
        model = UserRating
        fields = ['rating', 'comment']
    
    def __init__(self, *args, **kwargs):
        self.from_user = kwargs.pop('from_user', None)
        self.to_user = kwargs.pop('to_user', None)
        super().__init__(*args, **kwargs)
    
    def save(self, commit=True):
        rating = super().save(commit=False)
        rating.from_user = self.from_user
        rating.to_user = self.to_user
        if commit:
            rating.save()
        return rating
