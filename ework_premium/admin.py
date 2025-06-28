from django.contrib import admin
from .models import Package, Payment

@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = ['name', 'package_type', 'price_per_post', 'photo_addon_price', 'highlight_addon_price', 'auto_bump_addon_price', 'currency', 'is_active', 'order']
    list_filter = ['package_type', 'is_active', 'currency']
    list_editable = ['is_active', 'order']
    ordering = ['order']
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'description', 'package_type', 'is_active', 'order')
        }),
        ('Цены', {
            'fields': ('price_per_post', 'currency')
        }),
        ('Аддоны', {
            'fields': ('photo_addon_price', 'highlight_addon_price', 'auto_bump_addon_price')
        }),
        ('Настройки отображения', {
            'fields': ('highlight_color', 'duration_days')
        }),
    )

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['order_id', 'user', 'package', 'amount', 'status', 'created_at', 'paid_at']
    list_filter = ['status', 'package', 'created_at']
    readonly_fields = ['order_id', 'created_at', 'paid_at', 'telegram_payment_charge_id', 'telegram_provider_payment_charge_id']
    search_fields = ['order_id', 'user__username', 'user__email']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'package')
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ['user', 'package', 'amount']
        return self.readonly_fields


