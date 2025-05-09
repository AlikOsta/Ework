from django.db import models
from django.utils.translation import gettext_lazy as _

class Currency(models.Model):
    name = models.CharField(max_length=20, db_index=True, verbose_name=_("Название"), help_text=_("Название валюты"))
    code = models.CharField(max_length=8, db_index=True, verbose_name=_("Код"), help_text=_("Код валюты"))
    order = models.SmallIntegerField(default=0, db_index=True, verbose_name=_("Порядок"), help_text=_("Порядок валюты"))

    class Meta:
        verbose_name = _('Валюта')
        verbose_name_plural = _('Валюты')
        ordering = ['order']

    def __str__(self) -> str:
        return self.name
