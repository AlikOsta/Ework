from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.urls import reverse
from slugify import slugify

from .choices import STATUS_CHOICES
from .utils_img import process_image
from ework_locations.models import City,  Currency


class AbsPost(models.Model):
    title = models.CharField(max_length=200, verbose_name=_('Название'), help_text=_('Название объявления'))
    description = models.TextField(verbose_name=_('Описание'), help_text=_('Описание объявления'))
    image = models.ImageField(upload_to='post_img/', verbose_name=_('Изображение'), help_text=_('Изображение для объявления'))
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, verbose_name=_('Автор'), help_text=_('Автор объявления'))
    user_phone = models.CharField(max_length=20, verbose_name=_('Телефон'), help_text=_('Телефон автора объявления'), null=True, blank=True)
    city = models.ForeignKey(City, verbose_name=_('Город работы'), help_text=_('Город работы'), on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Дата создания"))    
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Дата обновления"))
    status = models.IntegerField(choices=STATUS_CHOICES, default=0, verbose_name=_('Статус'))
    is_premium = models.BooleanField(default=False, verbose_name=_('Премиум'), help_text=_('Премиум объявление'))
    price = models.IntegerField(verbose_name=_('Цена'), help_text=_('Цена'))
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT, verbose_name=_('Валюта'), help_text=_('Валюта объявления'))

    class Meta:
        abstract = True
        verbose_name = _("Объявление")
        verbose_name_plural = _("Объявления")
        ordering = ["-create_at"]

    def __str__(self):
        return self.title
    
    def get_absolute_url(self) -> str:
        return reverse("product:product_detail", kwargs={"pk": self.pk})
    
    def get_author_url(self) -> str:
        return reverse("user-detail", kwargs={"pk": self.user.pk})
    
    def get_view_count(self) -> int:
        return self.views.count()
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.image:
            processed = process_image(self.image, self.pk)

            if processed != self.image:
                self.image = processed
                super().save(update_fields=['image'])


class AbsCategory(models.Model):
    title = models.CharField(max_length=200, verbose_name=_('Название'), help_text=_('Название категории'))
    image = models.ImageField(upload_to='category_img/', verbose_name=_('Изображение'), help_text=_('Изображение для категории'))
    order = models.SmallIntegerField(default=0, db_index=True, verbose_name=_('Порядок'), help_text=_('Порядок категории'))
    slug = models.SlugField(max_length=50, unique=True, verbose_name=_('Слаг'), help_text=_('Слаг категории'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Дата создания"))

    class Meta:
        abstract = True
        verbose_name = _("Категория")
        verbose_name_plural = _("Категории")
        ordering = ['order']
        
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('category-detail', kwargs={'slug': self.slug})
    
    def get_count_products(self):
        products = self.products.filter(status=3)
        return products.count()


class AbsFavorite(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='%(app_label)s_%(class)s_favorites', verbose_name=_("Автор"))
    create_at = models.DateTimeField(auto_now=True, verbose_name=_("Дата создания"))

    class Meta:
        abstract = True
        verbose_name = _("Избранное")
        verbose_name_plural = _("Избранные")
        constraints = [
            models.UniqueConstraint(fields=['user', 'product'], name='unique_user_favorite')
        ]
        ordering = ["-create_at"]



class AbsProductView(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='%(app_label)s_%(class)s_views', verbose_name=_("Автор"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Дата создания"))

    class Meta:
        abstract = True
        verbose_name = _("Просмотры")
        verbose_name_plural = _("Просмотры")
        constraints = [
            models.UniqueConstraint(
                fields=['product', 'user'],
                name='unique_product_user_view'
            ),
        ]



