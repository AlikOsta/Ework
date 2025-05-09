from django.db import models
from django.utils.translation import gettext_lazy as _
from ework_post.models import AbsPost,AbsFavorite, AbsProductView


class PostServices(AbsPost):

    class Meta:
        pass


class FavoriteServices(AbsFavorite):
    product = models.ForeignKey("PostServices", on_delete=models.CASCADE, related_name='service_favorites', verbose_name=_("Объявление"))

    class Meta:
        pass    


class ProductViewServices(AbsProductView):
    product = models.ForeignKey("PostServices", on_delete=models.CASCADE, related_name='service_views', verbose_name=_("Объявление"))

    class Meta:
        pass



