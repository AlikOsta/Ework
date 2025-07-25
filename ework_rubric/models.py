from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify


class SuperRubric(models.Model):
    name = models.CharField(max_length=30, db_index=True, verbose_name=_('Название'), help_text=_('Название рубрики'))
    slug = models.SlugField(max_length=50, unique=True, db_index=True, verbose_name=_('Слаг'), help_text=_('Слаг рубрики'))
    order = models.SmallIntegerField(default=0, db_index=True, verbose_name=_('Порядок'), help_text=_('Порядок рубрики'))

    class Meta:
        app_label = "ework_config"
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
    

class SubRubric(models.Model):
    name = models.CharField(max_length=30, db_index=True, verbose_name=_('Название'), help_text=_('Название подрубрики'))
    icon = models.ImageField(upload_to='icons', blank=True, null=True, verbose_name=_('Иконка'), help_text=_('Иконка подрубрики'))
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

    class Meta:
        app_label = "ework_config"
        verbose_name = _("Подрубрика")
        verbose_name_plural = _("Подрубрики")
        ordering = ['order']


