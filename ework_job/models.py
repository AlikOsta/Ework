from django.db import models
from django.utils.translation import gettext_lazy as _
from ework_post.models import AbsPost, AbsFavorite, AbsProductView
from .choices import TYPE_OF_EMPLOYMENT_CHOICES, WORK_SCHEDULE_CHOICES, EXPERIENCE_CHOICES, WORK_FORMAT_CHOICES 


class PostJob(AbsPost):
    experience = models.IntegerField(choices=EXPERIENCE_CHOICES, default=0, verbose_name=_('Опыт работы')) 
    work_schedule = models.IntegerField(choices=WORK_SCHEDULE_CHOICES, default=0, verbose_name=_('График работы'))
    work_format = models.IntegerField(choices=WORK_FORMAT_CHOICES, default=0, verbose_name=_('Формат работы'))

    class Meta:
        pass


class FavoriteJob(AbsFavorite):
    product = models.ForeignKey("PostJob", on_delete=models.CASCADE, related_name='job_favorites', verbose_name=_("Объявление"))

    class Meta:
        pass


class ProductViewJob(AbsProductView):
    product = models.ForeignKey("PostJob", on_delete=models.CASCADE, related_name='job_views', verbose_name=_("Объявление"))

    class Meta:
        pass
    




