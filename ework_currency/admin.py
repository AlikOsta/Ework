from django.contrib import admin
from django.utils.html import format_html
from ework_currency.models import Currency


@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ('name', 'symbol', 'code', 'order')
    ordering = ('order', 'name')
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'symbol', 'code', 'order')
        }),
    )