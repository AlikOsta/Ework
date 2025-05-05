from django.db import models
from django.utils.translation import gettext_lazy as _
from ework_post.models import AbsPost, AbsCategory, AbsFavorite, AbsProductView



class PostJob(AbsPost):
    category = models.ForeignKey("CategoryJob", on_delete=models.CASCADE, related_name='products', verbose_name=_("Категория"))
    salary = models.IntegerField(verbose_name='Зарплата')
    experience = models.IntegerField(verbose_name='Опыт работы')
    work_schedule = models.CharField(max_length=200, verbose_name='График работы')

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



