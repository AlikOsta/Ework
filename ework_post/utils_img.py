import uuid
import logging
from io import BytesIO

from django.conf import settings
from django.core.files.base import ContentFile
from PIL import Image, ExifTags

logger = logging.getLogger(__name__)

DEFAULT_MAX_SIZE = getattr(settings, 'IMAGE_MAX_SIZE', (800, 800))
DEFAULT_FORMAT = getattr(settings, 'IMAGE_FORMAT', 'WEBP')
DEFAULT_QUALITY = getattr(settings, 'IMAGE_QUALITY', 65)

_ORIENTATION_TAG = next(
    (k for k, v in ExifTags.TAGS.items() if v == 'Orientation'),
    None
)


def apply_exif_orientation(image: Image.Image) -> Image.Image:
    """Поворот изображения согласно EXIF ориентации"""
    try:
        exif = image._getexif()
        if not exif or _ORIENTATION_TAG not in exif:
            return image

        orientation = exif[_ORIENTATION_TAG]
        if orientation == 3:
            image = image.rotate(180, expand=True)
        elif orientation == 6:
            image = image.rotate(270, expand=True)
        elif orientation == 8:
            image = image.rotate(90, expand=True)
    except Exception as e:
        logger.warning("Failed to apply EXIF orientation: %s", e)
    return image


def process_image(image_field, instance_id=None, max_size=None, img_format=None, quality=None):
    """
    Оптимизированная обработка изображений: изменение размера и сжатие
    """
    if not image_field:
        return None

    max_size = max_size or DEFAULT_MAX_SIZE
    img_format = (img_format or DEFAULT_FORMAT).upper()
    quality = quality or DEFAULT_QUALITY

    try:
        img = Image.open(image_field)
    except Exception as e:
        logger.error("Cannot open image %s: %s", image_field.name, e)
        return None

    # Применяем EXIF ориентацию
    img = apply_exif_orientation(img)

    # Изменяем размер если необходимо
    if img.width > max_size[0] or img.height > max_size[1]:
        img.thumbnail(max_size, Image.Resampling.LANCZOS)

    # Определяем формат и режим
    supports_alpha = img_format in ('WEBP', 'PNG')
    mode = 'RGBA' if supports_alpha and img.mode in ('RGBA', 'LA') else 'RGB'
    img = img.convert(mode)

    # Удаляем EXIF данные
    img.info.pop('exif', None)

    # Сохраняем в буфер
    buffer = BytesIO()
    save_kwargs = {'quality': quality}
    
    if img_format == 'WEBP':
        save_kwargs['lossless'] = supports_alpha and mode == 'RGBA'
        save_kwargs['method'] = 6
    if supports_alpha:
        save_kwargs['optimize'] = True

    try:
        img.save(buffer, format=img_format, **save_kwargs)
    except OSError as e:
        logger.warning("Optimize failed (%s); saving without optimize", e)
        img.save(buffer, format=img_format, quality=quality)

    buffer.seek(0)

    # Генерируем новое имя файла
    base, _ = image_field.name.rsplit('.', 1) if '.' in image_field.name else (image_field.name, '')
    prefix = f"{instance_id}_" if instance_id else ''
    unique_id = uuid.uuid4().hex[:8]
    new_name = f"{prefix}{base}_{unique_id}.{img_format.lower()}"

    return ContentFile(buffer.read(), name=new_name)