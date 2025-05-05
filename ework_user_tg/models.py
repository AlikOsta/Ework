
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.db.models import Avg
from django.core.validators import MinValueValidator, MaxValueValidator

from ework_locations.models import City


class TelegramUser(AbstractUser):
    telegram_id = models.BigIntegerField(unique=True, verbose_name=_('Telegram ID'), help_text=_("Telegram ID"))
    username = models.CharField(max_length=30, unique=True, verbose_name=_("Telegram Username"), help_text=_("Telegram имя"))
    first_name = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Имя"), help_text=_("Имя"))
    last_name = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Фамилия"), help_text=_("Фамилия"))
    photo_url = models.URLField(blank=True, null=True, verbose_name=_("URL фото"), help_text=_("URL на фото"))
    language =  models.CharField(max_length=5, default='ru', verbose_name=_("Язык"), help_text=_("Язык"))
    city = models.ForeignKey(City, on_delete=models.PROTECT, verbose_name=_("Город"),help_text=_("Город"), default=1)
    average_rating = models.FloatField(default=0, verbose_name=_("Средний рейтинг"), help_text=_("Средний рейтинг"))
    rating_count = models.PositiveIntegerField(default=0, verbose_name=_("Кол-во отзывов"), help_text=_("Кол-во отзывов"))
    phone = models.CharField(max_length=15, blank=True, unique=True, null=True, verbose_name=_("Номер телефона"), help_text=_("Номер телефона"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Дата создания"))    
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Дата обновления"))

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'telegram_id']

    class Meta:
        verbose_name = _("Пользователь")
        verbose_name_plural = _("Пользователи")
        ordering = ['-created_at']

    def __str__(self):
        return self.username
    
    def det_absolute_url(self):
        return reverse('user:user-profile', kwargs={'pk': self.pk})
    
    @property
    def average_rating(self):
        """Возвращает средний рейтинг пользователя"""
        return self.received_ratings.aggregate(avg_rating=Avg('rating'))['avg_rating'] or 0
    
    @property
    def ratings_count(self):
        """Возвращает количество полученных оценок"""
        return self.received_ratings.count()


class UserRating(models.Model):
    from_user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='given_ratings', verbose_name=_("Кого оцениваем"), help_text=_("Кого оцениваем"))
    to_user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='received_ratings', verbose_name=_("Кто оценивает"), help_text=_("Кто оценивает"))
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], verbose_name=_("Рейтинг"), help_text=_("Рейтинг"))
    comment = models.TextField(max_length=250, blank=True, null=True, verbose_name=_("Комментарий"), help_text=_("Комментарий"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Дата создания"), help_text=_("Дата создания"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Дата обновления"), help_text=_("Дата обновления"))

    class Meta:
        verbose_name = _("Оценка")
        verbose_name_plural = _("Оценки")
        constraints = [
            models.UniqueConstraint(
                fields=['from_user', 'to_user'],
                name='unique_user_rating'
            )
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.from_user.username} -> {self.to_user.username}: {self.rating}"
    
    def clean(self):
        from django.core.exceptions import ValidationError
        
        if self.from_user == self.to_user:
            raise ValidationError(_("Пользователь не может оценить сам себя"))


