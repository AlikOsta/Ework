from decimal import Decimal
from django.utils.translation import gettext_lazy as _
from .models import Package, FreePostRecord


class PricingCalculator:
    """Калькулятор стоимости публикации с аддонами"""
    
    def __init__(self, user, package=None):
        self.user = user
        self.package = package or self._get_default_package()
        
    def _get_default_package(self):
        """Получить пакет по умолчанию"""
        return Package.objects.filter(is_active=True, package_type='PAID').first()
    
    def can_post_free(self):
        """Проверить, может ли пользователь опубликовать бесплатно"""
        return FreePostRecord.can_user_post_free(self.user)
    
    def calculate_base_price(self):
        """Рассчитать базовую стоимость публикации"""
        if self.can_post_free():
            return Decimal('0.00')
        return self.package.price_per_post if self.package else Decimal('0.00')
    
    def calculate_addons_price(self, photo=False, highlight=False, auto_bump=False):
        """Рассчитать стоимость аддонов"""
        if not self.package:
            return Decimal('0.00')
            
        total = Decimal('0.00')
        
        if photo:
            total += self.package.photo_addon_price
        if highlight:
            total += self.package.highlight_addon_price
        if auto_bump:
            total += self.package.auto_bump_addon_price
            
        return total
    
    def calculate_total_price(self, photo=False, highlight=False, auto_bump=False):
        """Рассчитать общую стоимость"""
        base_price = self.calculate_base_price()
        addons_price = self.calculate_addons_price(photo, highlight, auto_bump)
        return base_price + addons_price
    
    def get_pricing_breakdown(self, photo=False, highlight=False, auto_bump=False):
        """Получить детальную разбивку цен"""
        base_price = self.calculate_base_price()
        addons_price = self.calculate_addons_price(photo, highlight, auto_bump)
        total_price = base_price + addons_price
        
        breakdown = {
            'can_post_free': self.can_post_free(),
            'base_price': base_price,
            'addons': {
                'photo': {
                    'selected': photo,
                    'price': self.package.photo_addon_price if photo and self.package else Decimal('0.00'),
                    'description': _('Добавить фото')
                },
                'highlight': {
                    'selected': highlight,
                    'price': self.package.highlight_addon_price if highlight and self.package else Decimal('0.00'),
                    'description': _('Выделить цветом')
                },
                'auto_bump': {
                    'selected': auto_bump,
                    'price': self.package.auto_bump_addon_price if auto_bump and self.package else Decimal('0.00'),
                    'description': _('Автоподнятие')
                }
            },
            'addons_total': addons_price,
            'total_price': total_price,
            'currency': self.package.currency if self.package else None,
            'is_free': total_price == 0
        }
        
        return breakdown
    
    def get_button_config(self, photo=False, highlight=False, auto_bump=False):
        """Получить конфигурацию кнопки оплаты"""
        total_price = self.calculate_total_price(photo, highlight, auto_bump)
        currency = self.package.currency if self.package else None
        
        if total_price == 0:
            return {
                'text': _('Опубликовать бесплатно'),
                'class': 'btn btn-primary',
                'action': 'publish_free'
            }
        else:
            currency_symbol = currency.symbol if currency else '$'
            return {
                'text': _('Оплатить {price} {currency}').format(
                    price=total_price,
                    currency=currency_symbol
                ),
                'class': 'btn btn-success',
                'action': 'pay_and_publish'
            }


def create_payment_for_post(user, package, photo=False, highlight=False, auto_bump=False, copy_from_id=None):
    """Создать платеж для публикации поста с аддонами"""
    from .models import Payment
    if copy_from_id is not None:
        try:
            from ework_post.models import AbsPost
            original_post = AbsPost.objects.get(id=copy_from_id, user=user)
            if (original_post.package and original_post.package.is_paid() and 
                (original_post.has_photo_addon or original_post.has_highlight_addon or original_post.has_auto_bump_addon)):
                photo = original_post.has_photo_addon
                highlight = original_post.has_highlight_addon  
                auto_bump = original_post.has_auto_bump_addon
        except AbsPost.DoesNotExist:
            print(f"⚠️ Оригинальный пост {copy_from_id} не найден")
    calculator = PricingCalculator(user, package)
    total_price = calculator.calculate_total_price(photo, highlight, auto_bump)
    if total_price == 0:
        return None 
    payment = Payment.objects.create(
        user=user,
        package=package,
        amount=total_price,
        order_id=Payment.generate_order_id(user.id)
    )
    payment.set_addons(photo=photo, highlight=highlight, auto_bump=auto_bump)
    if copy_from_id is not None:
        if not payment.addons_data:
            payment.addons_data = {}
        payment.addons_data['copy_from_id'] = copy_from_id
    payment.save()
    
    return payment
