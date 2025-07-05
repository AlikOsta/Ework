
from django.utils.translation import gettext_lazy as _
from ework_post.models import AbsPost


class PostServices(AbsPost):

    class Meta:
        app_label = "ework_post"
        verbose_name = _("Услуга")
        verbose_name_plural = _("Услуги")






