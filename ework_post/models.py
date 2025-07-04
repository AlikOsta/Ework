from django.db import models
from django.forms import ValidationError
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

from polymorphic.models import PolymorphicModel
from polymorphic.managers import PolymorphicManager

from .choices import STATUS_CHOICES
from .utils_img import process_image
from ework_locations.models import City
from ework_currency.models import Currency
from ework_rubric.models import SubRubric
from ework_premium.models import Package


phone_regex = RegexValidator(
    regex=r'^\+?1?\d{9,15}$',
    message=_("Номер телефона должен быть в формате: '+3(xxx)xxx-xx-xx'")
)


class AbsPost(PolymorphicModel):
    """Оптимизированная абстрактная модель поста"""
    objects = PolymorphicManager()
    
    title = models.CharField(max_length=50, db_index=True, verbose_name=_('Название'))
    description = models.TextField(db_index=True, verbose_name=_('Описание'))
    image = models.ImageField(upload_to='post_img/', verbose_name=_('Изображение'), null=True, blank=True) 
    price = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(99999999)], db_index=True, verbose_name=_('Сумма'))
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT, verbose_name=_('Валюта'))
    sub_rubric = models.ForeignKey(SubRubric, on_delete=models.PROTECT, db_index=True, related_name='%(app_label)s_%(class)s_posts', verbose_name=_('Рубрика'))
    city = models.ForeignKey(City, verbose_name=_('Город работы'), db_index=True, on_delete=models.PROTECT)
    address = models.CharField(max_length=255, blank=True, null=True, verbose_name=_('Адрес'))
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, db_index=True, verbose_name=_('Автор'))
    user_phone = models.CharField(max_length=20, validators=[phone_regex], verbose_name=_('Телефон'), null=True, blank=True)
    status = models.IntegerField(choices=STATUS_CHOICES, default=0, db_index=True, verbose_name=_('Статус'))
    is_premium = models.BooleanField(default=False, db_index=True, verbose_name=_('Цветной фон карточки'))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Дата создания"))    
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Дата обновления"))
    is_deleted = models.BooleanField(default=False, db_index=True, verbose_name=_("Удалено"))
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Дата удаления"))
    package = models.ForeignKey(Package, on_delete=models.PROTECT, null=True, blank=True, verbose_name=_('Тариф'))
    
    # Поля для промо-функций
    has_photo_addon = models.BooleanField(default=False, verbose_name=_("Аддон фото"))
    has_highlight_addon = models.BooleanField(default=False, verbose_name=_("Аддон выделения"))
    has_auto_bump_addon = models.BooleanField(default=False, verbose_name=_("Аддон автоподнятия"))
    
    # Даты истечения промо
    highlight_expires_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Выделение до"))
    auto_bump_expires_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Автоподнятие до"))
    last_bump_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Последнее поднятие"))

    class Meta:
        verbose_name = _("Объявление")
        verbose_name_plural = _("Объявления")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['sub_rubric', 'status']),
            models.Index(fields=['city', 'status']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['is_premium', 'status', 'created_at']),
        ]

    def __str__(self) -> str:
        return self.title
    
    def get_absolute_url(self) -> str:
        return reverse("core:product_detail", kwargs={"pk": self.pk})
    
    def get_author_url(self) -> str:
        return reverse("users:author_profile", kwargs={"author_id": self.user.pk})

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Обрабатываем изображение только при первом сохранении
        if self.image and not hasattr(self, '_image_processed'):
            processed = process_image(self.image, self.pk)
            if processed != self.image:
                self.image = processed
                self._image_processed = True
                super().save(update_fields=['image'])
    
    def soft_delete(self):
        """Мягкое удаление поста"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at'])
    
    def set_addons(self, photo=False, highlight=False, auto_bump=False):
        """Установить аддоны для поста"""
        from datetime import timedelta
        
        self.has_photo_addon = photo
        self.has_highlight_addon = highlight
        self.has_auto_bump_addon = auto_bump
        
        # Если есть выделение цветом - делаем пост премиум
        self.is_premium = highlight
        
        # Устанавливаем время истечения для аддонов
        now = timezone.now()
        
        if highlight:
            self.highlight_expires_at = now + timedelta(days=3)
        
        if auto_bump:
            self.auto_bump_expires_at = now + timedelta(days=7)

    def apply_addons_from_payment(self, payment):
        """Применить аддоны из платежа к посту"""
        self.set_addons(
            photo=payment.has_photo_addon(),
            highlight=payment.has_highlight_addon(),
            auto_bump=payment.has_auto_bump_addon()
        )
        self.save(update_fields=[
            'has_photo_addon', 'has_highlight_addon', 'has_auto_bump_addon',
            'highlight_expires_at', 'auto_bump_expires_at', 'is_premium'
        ])
    
    def is_highlight_active(self):
        """Проверить, активно ли выделение"""
        return (self.has_highlight_addon and 
                self.highlight_expires_at and 
                self.highlight_expires_at > timezone.now())
    
    def is_auto_bump_active(self):
        """Проверить, активно ли автоподнятие"""
        return (self.has_auto_bump_addon and 
                self.auto_bump_expires_at and 
                self.auto_bump_expires_at > timezone.now())
    
    def can_be_bumped(self):
        """Проверить, можно ли поднять пост (прошло 12 часов)"""
        from datetime import timedelta
        
        if not self.is_auto_bump_active():
            return False
            
        if not self.last_bump_at:
            return True
            
        return self.last_bump_at + timedelta(hours=12) <= timezone.now()
    
    def bump_post(self):
        """Поднять пост в топ"""
        self.last_bump_at = timezone.now()
        self.save(update_fields=['last_bump_at'])


class PostView(models.Model):
    """Модель для просмотров постов"""
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, verbose_name=_("Пользователь"))
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, verbose_name=_("Тип контента"))
    object_id = models.PositiveIntegerField(verbose_name=_("ID объекта"))
    post = GenericForeignKey('content_type', 'object_id')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Дата просмотра"))

    class Meta:
        verbose_name = _("Просмотр")
        verbose_name_plural = _("Просмотры")
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'content_type', 'object_id'],
                name='unique_user_post_view'
            ),
        ]
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['user', 'created_at']),
        ]

    def __str__(self) -> str:
        return f"{self.user.username} просмотрел {self.post}"


class Favorite(models.Model):
    """Модель избранных постов"""
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='favorites', verbose_name=_("Пользователь"))
    post = models.ForeignKey(AbsPost, on_delete=models.CASCADE, related_name='favorited_by', verbose_name=_("Пост"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Дата добавления"))

    class Meta:
        verbose_name = _("Избранное")
        verbose_name_plural = _("Избранные")
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'post'],
                name='unique_user_post_favorite'
            ),
        ]
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['post', 'created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} → {self.post.title}"


class BannerPost(models.Model):
    """Модель баннеров"""
    title = models.CharField(max_length=50, verbose_name=_("Заголовок"), db_index=True)
    description = models.TextField(verbose_name=_('Описание'), blank=True, null=True)
    link = models.URLField(max_length=200, verbose_name=_('Ссылка'), blank=True, null=True)
    image = models.ImageField(upload_to='banner/', verbose_name=_('Изображение'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Дата создания"))
    is_active = models.BooleanField(default=True, db_index=True, verbose_name=_("Активно"))
    order = models.PositiveIntegerField(default=0, db_index=True, verbose_name=_("Порядок отображения"))

    class Meta:
        app_label = 'ework_premium'
        verbose_name = _("Баннер")
        verbose_name_plural = _("Баннеры")
        ordering = ["order", "-created_at"]
        indexes = [
            models.Index(fields=['is_active', 'order']),
        ]
    
    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.image:
            processed = process_image(self.image, self.pk)
            if processed != self.image:
                self.image = processed
                super().save(update_fields=['image'])