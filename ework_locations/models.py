from django.db import models
from django.utils.translation import gettext_lazy as _


class City(models.Model):
    name = models.CharField(max_length=50, db_index=True, verbose_name=_("Название города"), help_text=_("Название города"))
    order = models.SmallIntegerField(default=0, db_index=True, verbose_name=_("Порядок"), help_text=_("Порядок города"))

    class Meta:
        verbose_name = _("Город")
        verbose_name_plural = _("Города")
        ordering = ['order']

    def __str__(self) -> str:
        return self.name
    
