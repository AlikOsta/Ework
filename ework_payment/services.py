"""
Сервисы для обработки платежей через Telegram
"""
import logging
from decimal import Decimal
from django.conf import settings
from django.utils import timezone
from ework_premium.models import Payment, Package, FreePostRecord
from ework_post.models import AbsPost

logger = logging.getLogger(__name__)


class PaymentService:
    """Сервис для обработки платежей"""
    
    @staticmethod
    def create_payment(user, package, post=None):
        """Создать платеж для тарифа"""
        try:
            # Проверяем, что тариф платный
            if package.is_free():
                raise ValueError("Нельзя создать платеж для бесплатного тарифа")
            
            # Генерируем уникальный ID заказа
            order_id = Payment.generate_order_id(user.id)
            
            # Создаем запись о платеже
            payment = Payment.objects.create(
                user=user,
                package=package,
                amount=package.price_per_post,
                order_id=order_id,
                status='pending'
            )
            
            logger.info(f"Создан платеж {payment.order_id} для пользователя {user.username}")
            return payment
            
        except Exception as e:
            logger.error(f"Ошибка создания платежа: {e}")
            raise
    
    @staticmethod
    def process_successful_payment(payment, telegram_charge_id=None, provider_charge_id=None):
        """Обработать успешный платеж"""
        try:
            # Отмечаем платеж как оплаченный
            payment.mark_as_paid(telegram_charge_id, provider_charge_id)
            
            logger.info(f"Платеж {payment.order_id} успешно обработан")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка обработки платежа {payment.order_id}: {e}")
            return False
    
    @staticmethod
    def process_failed_payment(payment, reason=None):
        """Обработать неудачный платеж"""
        try:
            payment.mark_as_failed()
            
            logger.warning(f"Платеж {payment.order_id} отмечен как неудачный: {reason}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка обработки неудачного платежа {payment.order_id}: {e}")
            return False
    
    @staticmethod
    def refund_payment(payment, reason=None):
        """Возврат средств (логическая операция)"""
        try:
            # В реальном приложении здесь был бы API вызов к платежной системе
            # Пока просто логируем
            payment.status = 'refunded'
            payment.save(update_fields=['status'])
            
            logger.info(f"Возврат средств по платежу {payment.order_id}: {reason}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка возврата средств по платежу {payment.order_id}: {e}")
            return False


class PostPublicationService:
    """Сервис для публикации постов с учетом тарифов"""
    
    @staticmethod
    def can_publish_post(user, package):
        """Проверить, может ли пользователь опубликовать пост с данным тарифом"""
        if package.is_free():
            return FreePostRecord.can_user_post_free(user)
        return True  # Платные тарифы всегда доступны после оплаты
    
    @staticmethod
    def publish_post(post, package, payment=None):
        """Опубликовать пост согласно тарифу"""
        try:
            # Устанавливаем тариф поста
            post.package = package
            
            # Если это премиум тариф с выделением цветом
            if package.highlight_color:
                post.is_premium = True
            
            # Отправляем на модерацию
            post.status = 0  # На модерации
            post.save()
            
            # Если это бесплатный тариф, отмечаем использование
            if package.is_free():
                FreePostRecord.use_free_post(post.user, post)
            
            logger.info(f"Пост {post.id} отправлен на модерацию с тарифом {package.name}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка публикации поста {post.id}: {e}")
            return False
    
    @staticmethod
    def handle_moderation_rejection(post):
        """Обработать отклонение поста модерацией"""
        try:
            # Если был платеж, возвращаем деньги
            if post.package and post.package.is_paid():
                # Ищем платеж для этого поста
                payment = Payment.objects.filter(
                    user=post.user,
                    package=post.package,
                    status='paid'
                ).order_by('-created_at').first()
                
                if payment:
                    PaymentService.refund_payment(payment, "Пост не прошел модерацию")
            
            # Если это был бесплатный пост, возвращаем возможность бесплатной публикации
            if post.package and post.package.is_free():
                free_record = FreePostRecord.get_user_free_post_this_week(post.user)
                if free_record and free_record.post == post:
                    free_record.delete()
            
            logger.info(f"Обработано отклонение поста {post.id} модерацией")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка обработки отклонения поста {post.id}: {e}")
            return False


class TelegramPaymentService:
    """Сервис для работы с Telegram Payments API"""
    
    @staticmethod
    def create_invoice_payload(payment):
        """Создать payload для счета Telegram"""
        return {
            'title': f"Тариф: {payment.package.name}",
            'description': payment.package.description,
            'payload': payment.get_payload(),
            'provider_token': settings.TELEGRAM_PAYMENT_TOKEN if hasattr(settings, 'TELEGRAM_PAYMENT_TOKEN') else '',
            'currency': payment.package.currency.code if payment.package.currency else 'UAH',
            'prices': [
                {
                    'label': payment.package.name,
                    'amount': int(payment.amount * 100)  # Telegram требует сумму в копейках
                }
            ]
        }
    
    @staticmethod
    def verify_payment(payment_data):
        """Проверить данные платежа от Telegram"""
        # В реальном приложении здесь была бы проверка подписи и других данных
        # Пока просто возвращаем True
        return True