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
    
    def calculate_addons_price(self, photo=False, highlight=False, existing_post=None):
        """Рассчитать стоимость аддонов с учетом существующего поста"""
        if not self.package:
            return Decimal('0.00')
            
        total = Decimal('0.00')
        
        # Если есть существующий пост, проверяем активные услуги
        if existing_post:
            addons_info = existing_post.get_addons_info()
            
            # Добавляем стоимость только за новые или истекшие услуги
            if photo and not addons_info['photo']['active']:
                total += self.package.photo_addon_price
            if highlight and not addons_info['highlight']['active']:
                total += self.package.highlight_addon_price
        else:
            # Для нового поста - обычная логика
            if photo:
                total += self.package.photo_addon_price
            if highlight:
                total += self.package.highlight_addon_price
            
        return total
    
    def calculate_total_price(self, photo=False, highlight=False, existing_post=None):
        """Рассчитать общую стоимость с учетом существующего поста"""
        if existing_post:
            # Для редактирования - только стоимость новых аддонов
            base_price = Decimal('0.00')
            addons_price = self.calculate_addons_price(photo, highlight, existing_post)
        else:
            # Для нового поста - обычная логика
            base_price = self.calculate_base_price()
            addons_price = self.calculate_addons_price(photo, highlight)
            
        return base_price + addons_price
    
    def get_pricing_breakdown(self, photo=False, highlight=False, existing_post=None):
        """Получить детальную разбивку цен с учетом существующего поста"""
        from ework_config.models import SiteConfig
        config = SiteConfig.get_config()
        
        if existing_post:
            base_price = Decimal('0.00')
            addons_info = existing_post.get_addons_info()
        else:
            base_price = self.calculate_base_price()
            addons_info = None
            
        addons_price = self.calculate_addons_price(photo, highlight, existing_post)
        total_price = base_price + addons_price
        
        breakdown = {
            'can_post_free': self.can_post_free() if not existing_post else False,
            'base_price': base_price,
            'is_update': existing_post is not None,
            'addons': {
                'photo': {
                    'selected': photo,
                    'price': self.package.photo_addon_price if photo and self.package else Decimal('0.00'),
                    'description': _(f'Добавить фото ({config.photo_addon_duration_days} дней)'),
                    'active': addons_info['photo']['active'] if addons_info else False,
                    'expires_at': addons_info['photo']['expires_at'] if addons_info else None,
                    'days_left': addons_info['photo']['days_left'] if addons_info else 0,
                    'needs_payment': photo and (not addons_info or not addons_info['photo']['active'])
                },
                'highlight': {
                    'selected': highlight,
                    'price': self.package.highlight_addon_price if highlight and self.package else Decimal('0.00'),
                    'description': _(f'Выделить цветом ({config.highlight_addon_duration_days} дня)'),
                    'active': addons_info['highlight']['active'] if addons_info else False,
                    'expires_at': addons_info['highlight']['expires_at'] if addons_info else None,
                    'days_left': addons_info['highlight']['days_left'] if addons_info else 0,
                    'needs_payment': highlight and (not addons_info or not addons_info['highlight']['active'])
                }
            },
            'addons_total': addons_price,
            'total_price': total_price,
            'currency': self.package.currency if self.package else None,
            'is_free': total_price == 0
        }
        
        return breakdown
    
    def get_button_config(self, photo=False, highlight=False, existing_post=None):
        """Получить конфигурацию кнопки оплаты с учетом существующего поста"""
        total_price = self.calculate_total_price(photo, highlight, existing_post)
        currency = self.package.currency if self.package else None
        
        if existing_post:
            # Для редактирования
            if total_price == 0:
                return {
                    'text': _('Сохранить изменения'),
                    'class': 'btn btn-primary',
                    'action': 'update_free'
                }
            else:
                currency_symbol = currency.symbol if currency else '$'
                return {
                    'text': _('Доплатить {price} {currency} и сохранить').format(
                        price=total_price,
                        currency=currency_symbol
                    ),
                    'class': 'btn btn-success',
                    'action': 'pay_and_update'
                }
        else:
            # Для нового поста
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


def create_payment_for_post(user, package, photo=False, highlight=False, auto_bump=False):
    """Создать платеж для публикации поста с аддонами"""
    from .models import Payment
    
    calculator = PricingCalculator(user, package)
    total_price = calculator.calculate_total_price(photo, highlight, auto_bump)
    
    if total_price == 0:
        return None  # Бесплатная публикация
    
    payment = Payment.objects.create(
        user=user,
        package=package,
        amount=total_price,
        order_id=Payment.generate_order_id(user.id)
    )
    
    # Сохранить информацию об аддонах
    payment.set_addons(photo=photo, highlight=highlight, auto_bump=auto_bump)
    payment.save()
    
    return payment
