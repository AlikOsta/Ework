from django import template
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from ework_post.models import Favorite

register = template.Library()

@register.filter
def get_ct(obj):
    """
    Возвращает строку 'app_label.model' для переданного объекта.
    """
    ct = ContentType.objects.get_for_model(obj)
    return f"{ct.app_label}.{ct.model}"

@register.filter
def get_is_fav(obj, user):
    """
    Проверяет, добавил ли пользователь объекy в избранное.
    """
    if not user or not user.is_authenticated:
        return False
    ct = ContentType.objects.get_for_model(obj)
    return Favorite.objects.filter(
        user=user,
        content_type=ct,
        object_id=obj.pk
    ).exists()

@register.filter
def get_fav_count(obj):
    """
    Возвращает количество добавлений объекта obj в избранное.
    """
    ct = ContentType.objects.get_for_model(obj)
    return Favorite.objects.filter(
        content_type=ct,
        object_id=obj.pk
    ).count()
