from django.contrib import admin
from django.utils.html import format_html
from .models import Currency


@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ('name', 'symbol', 'code', 'order')
    search_fields = ('name', 'code', 'symbol')
    ordering = ('order', 'name')
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'symbol', 'code', 'order')
        }),
    )
