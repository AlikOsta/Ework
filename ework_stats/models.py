from django.db import models
from django.utils.translation import gettext_lazy as _

class DailyStats(models.Model):
    date = models.DateField(unique=True)
    new_users = models.IntegerField(default=0)
    new_posts = models.IntegerField(default=0)
    post_views = models.IntegerField(default=0)
    favorites_added = models.IntegerField(default=0)
    
    class Meta:
        verbose_name = _("Статистика")
        verbose_name_plural = _("Статистика")
        ordering = ['-date']
    
    def __str__(self):
        return f"Статистика за {self.date}"
