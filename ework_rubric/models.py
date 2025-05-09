from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from slugify import slugify


class Rubric(models.Model):
    name = models.CharField(max_length=30, db_index=True, verbose_name=_('Название'), help_text=_('Название рубрики'))
    image  = models.ImageField(upload_to='rubric_img/', verbose_name=_('Изображение'), help_text=_('Изображение для рубрики'))
    slug = models.SlugField(max_length=50, unique=True, db_index=True, verbose_name=_('Слаг'), help_text=_('Слаг рубрики'))
    order = models.SmallIntegerField(default=0, db_index=True, verbose_name=_('Порядок'), help_text=_('Порядок рубрики'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Дата создания"))
    super_rubric = models.ForeignKey('SuperRubric', on_delete=models.PROTECT, null=True, blank=True, verbose_name=_('Родительская рубрика'), help_text=_('Родительская рубрика'))

    class Meta:
        verbose_name = _("Рубрика")
        verbose_name_plural = _("Рубрики")
        ordering = ['order']

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self) -> str:
        return reverse('rubric_detail', kwargs={'slug': self.slug})
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_count_products(self) -> int:
        products = self.products.filter(status=3)
        return products.count()


class SuperRubricManager(models.Manager):
    
    def get_queryset(self):
        return super().get_queryset().filter(super_rubric__isnull=True)
    

class SuperRubric(Rubric):
    objects = SuperRubricManager()

    class Meta:
        proxy = True
        ordering = ('order', 'name')
        verbose_name = _("Суперрубрика")
        verbose_name_plural = _("Суперрубрики")

    def __str__(self) -> str:
        return self.name
    

class SubRubricManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(super_rubric__isnull=False)
    

class SubRubric(Rubric):
    objects = SubRubricManager()

    class Meta:
        proxy = True
        ordering = ('super_rubric__order', 'super_rubric__name', 'order', 'name')
        verbose_name = _("Подрубрика")
        verbose_name_plural = _("Подрубрики")

    def __str__(self) -> str:
            return '%s - %s' % (self.super_rubric.name, self.name)