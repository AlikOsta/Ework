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
