from django.db import models
from django.utils.translation import gettext_lazy as _
from ework_post.models import AbsPost, AbsCategory, AbsFavorite, AbsProductView
from .choices import TYPE_OF_EMPLOYMENT_CHOICES, WORK_SCHEDULE_CHOICES, EXPERIENCE_CHOICES, WORK_FORMAT_CHOICES 


class PostJob(AbsPost):
    category = models.ForeignKey("CategoryJob", on_delete=models.CASCADE, related_name='products', verbose_name=_("Категория"))
    experience = models.IntegerField(choices=EXPERIENCE_CHOICES, default=0, verbose_name=_('Опыт работы')) 
    work_schedule = models.IntegerField(choices=WORK_SCHEDULE_CHOICES, default=0, verbose_name=_('График работы'))
    type_of_work = models.IntegerField(choices=TYPE_OF_EMPLOYMENT_CHOICES, default=0, verbose_name=_('Тип занятости'))
    work_format = models.IntegerField(choices=WORK_FORMAT_CHOICES, default=0, verbose_name=_('Формат работы'))

    class Meta:
        pass


class CategoryJob(AbsCategory):
    class Meta:
        pass


class FavoriteJob(AbsFavorite):
    product = models.ForeignKey("PostJob", on_delete=models.CASCADE, related_name='job_favorites', verbose_name=_("Объявление"))

    class Meta:
        pass

    def __str__(self) -> str:
       return f"{self.user.username} - {self.product.title}"


class ProductViewJob(AbsProductView):
    product = models.ForeignKey("PostJob", on_delete=models.CASCADE, related_name='job_views', verbose_name=_("Объявление"))

    class Meta:
        pass
    
    def __str__(self) -> str:
        return f"{self.product.title} - {self.user.username}"



