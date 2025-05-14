from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from slugify import slugify


class SuperRubric(models.Model):
    name = models.CharField(max_length=30, db_index=True, verbose_name=_('Название'), help_text=_('Название рубрики'))
    image  = models.ImageField(upload_to='rubric_img/', verbose_name=_('Изображение'), help_text=_('Изображение для рубрики'))
    slug = models.SlugField(max_length=50, unique=True, db_index=True, verbose_name=_('Слаг'), help_text=_('Слаг рубрики'))
    order = models.SmallIntegerField(default=0, db_index=True, verbose_name=_('Порядок'), help_text=_('Порядок рубрики'))

    class Meta:
        verbose_name = _("Категория")
        verbose_name_plural = _("Категории")
        ordering = ['order']
        
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('category-detail', kwargs={'slug': self.slug})
    
    def get_products(self):
        products = self.products.filter(status=3)
        return products
    

class SubRubric(models.Model):
    name = models.CharField(max_length=30, db_index=True, verbose_name=_('Название'), help_text=_('Название подрубрики'))
    image  = models.ImageField(upload_to='sub_rubric_img/', verbose_name=_('Изображение'), help_text=_('Изображение для подрубрики'))
    slug = models.SlugField(max_length=50, unique=True, db_index=True, verbose_name=_('Слаг'), help_text=_('Слаг подрубрики'))
    order = models.SmallIntegerField(default=0, db_index=True, verbose_name=_('Порядок'), help_text=_('Порядок подрубрики'))
    super_rubric = models.ForeignKey(SuperRubric, on_delete=models.PROTECT, related_name='sub_rubrics', verbose_name=_('Категория'), help_text=_('Категория подрубрики'))

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('subcategory-detail', kwargs={'slug': self.slug})

    def get_products(self):
        products = self.products.filter(status=3)
        return products

    
    class Meta:
        verbose_name = _("Подрубрика")
        verbose_name_plural = _("Подрубрики")
        ordering = ['order']


