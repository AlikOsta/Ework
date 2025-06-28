from django.db import models
from django.utils.translation import gettext_lazy as _
from ework_post.models import AbsPost
from .choices import WORK_SCHEDULE_CHOICES, EXPERIENCE_CHOICES, WORK_FORMAT_CHOICES 


class PostJob(AbsPost):
    experience = models.IntegerField(choices=EXPERIENCE_CHOICES, default=0, verbose_name=_('Опыт работы')) 
    work_schedule = models.IntegerField(choices=WORK_SCHEDULE_CHOICES, default=0, verbose_name=_('График работы'))
    work_format = models.IntegerField(choices=WORK_FORMAT_CHOICES, default=0, verbose_name=_('Формат работы'))

    class Meta:
        app_label = "ework_post"
        verbose_name = _("Вакансия")
        verbose_name_plural = _("Вакансии")


    




