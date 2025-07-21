from django.db import models
from django.utils.translation import gettext_lazy as _


CHOICES_CITY = [
    (0, _("Київ")),
    (1, _("Дніпро")),
    (2, _("Хмельницький")),
    (3, _("Миколаїв")),
    (4, _("Вінниця")),
    (5, _("Харків")),
    (6, _("Одеса")),
    (7, _("Запоріжжя")),
    (8, _("Львів")),
    (9, _("Полтава")),
    (10, _("Житомир")),
    (11, _("Інше")),
]

class City(models.Model):
    name = models.IntegerField(choices=CHOICES_CITY, default=0, verbose_name=_('Название города'))
    order = models.SmallIntegerField(default=0, db_index=True, verbose_name=_("Порядок"), help_text=_("Порядок города"))

    class Meta:
        app_label = "ework_config"
        verbose_name = _("Город")
        verbose_name_plural = _("Города")
        ordering = ['order']

    def __str__(self) -> str:
        return self.name
    
