from django.utils.translation import gettext_lazy as _


STATUS_CHOICES = [
        (-1, _('Черновик')),
        (0, _('Не проверено')),
        (1, _('На модерации')),
        (2, _('Отклонено')),
        (3, _('Опубликовано')),
        (4, _('Архив')),
    ]