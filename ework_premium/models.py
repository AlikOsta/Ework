from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _


class Package(models.Model):
    """
    Описывает тарифный пакет (Классика, Старт, Оптимальный, Премиум, Баннер).
    """
    name = models.CharField(max_length=50, unique=True, verbose_name=_("Название тарифа"), help_text=_("Название тарифа"))
    description = models.TextField(verbose_name=_("Описание тарифа"), help_text=_("Описание тарифа"))
    price_per_post = models.DecimalField(max_digits=8, decimal_places=2, verbose_name=_("Цена за объявление"), help_text=_("Цена за объявление"))
    highlight_color = models.CharField(max_length=7, blank=True,verbose_name=_("HEX-код цвета для выделения объявления"), help_text=_("HEX-код цвета для выделения объявления"))
    icon_flag = models.CharField(max_length=50, blank=True, verbose_name=_("Имя CSS-класса или значка (например, ⭐️ для Премиум)"), help_text=_("Имя CSS-класса или значка (например, ⭐️ для Премиум)"))

    def __str__(self):
        return self.name


class Subscription(models.Model):
    """
    Фиксирует факт покупки пакета пользователем.
    """
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='subscriptions')
    package = models.ForeignKey(Package, on_delete=models.PROTECT)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField()
    remaining_posts = models.PositiveIntegerField(help_text="Сколько постов ещё можно разместить по этому пакету")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user} — {self.package}"


class FreePostRecord(models.Model):
    """
    Отмечает, что пользователь использовал бесплатное размещение на текущей неделе.
    """
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='free_posts')
    week_start = models.DateField(help_text="Дата понедельника этой недели")
    used = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'week_start')

    def __str__(self):
        status = 'used' if self.used else 'free'
        return f"{self.user} @ {self.week_start} ({status})"
