# user_capybara/verify_telegram_init_data.py
import hmac
import hashlib
import logging
from urllib.parse import unquote, parse_qsl

logger = logging.getLogger(__name__)

def verify_init_data(init_data: str, bot_token: str) -> bool:
    """
    Проверяет подпись initData, возвращает True, если данные подлинные.
    """
    if not bot_token:
        logger.error("verify_init_data: bot_token is empty or None")
        return False

    try:
        decoded = unquote(init_data)
        params = dict(parse_qsl(decoded, keep_blank_values=True))
        hash_sent = params.pop("hash", None)
        if not hash_sent:
            logger.error("verify_init_data: no hash in init_data")
            return False

        data_check_arr = [f"{k}={v}" for k, v in sorted(params.items())]
        data_check_string = "\n".join(data_check_arr)

        secret_key = hmac.new(
            key=b"WebAppData",
            msg=bot_token.encode(),
            digestmod=hashlib.sha256
        ).digest()


        computed_hash = hmac.new(
            key=secret_key,
            msg=data_check_string.encode(),
            digestmod=hashlib.sha256
        ).hexdigest()

        valid = computed_hash == hash_sent
        if not valid:
            logger.error(
                "verify_init_data: hash mismatch; computed %s, sent %s",
                computed_hash, hash_sent
            )
        return valid

    except Exception as e:
        logger.exception("verify_init_data: unexpected error")
        return False
