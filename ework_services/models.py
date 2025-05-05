from django.db import models
from django.utils.translation import gettext_lazy as _
from ework_post.models import AbsPost, AbsCategory, AbsFavorite, AbsProductView



class PostServices(AbsPost):
    category = models.ForeignKey("CategoryServices", on_delete=models.CASCADE, related_name='products', verbose_name=_("Категория"))

    class Meta:
        pass


class CategoryServices(AbsCategory):
    class Meta:
        pass


class FavoriteServices(AbsFavorite):
    product = models.ForeignKey("PostServices", on_delete=models.CASCADE, related_name='service_favorites', verbose_name=_("Объявление"))

    class Meta:
        pass    

    def __str__(self) -> str:
       return f"{self.user.username} - {self.product.title}"


class ProductViewServices(AbsProductView):
    product = models.ForeignKey("PostServices", on_delete=models.CASCADE, related_name='service_views', verbose_name=_("Объявление"))

    class Meta:
        pass

    def __str__(self) -> str:
        return f"{self.product.title} - {self.user.username}"



