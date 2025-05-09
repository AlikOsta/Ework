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
    """
    Rotate the image according to its EXIF orientation tag.
    """
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


def process_image(
    image_field,
    instance_id=None,
    max_size=None,
    img_format=None,
    quality=None
) -> ContentFile | None:
    """
    Open, auto-orient, resize, and compress an uploaded image file.

    :param image_field: Uploaded file-like object (e.g. Django ImageField file)
    :param instance_id: Optional identifier to prefix output filename
    :param max_size: (width, height) tuple. Defaults to settings or 800x800
    :param img_format: Output format (e.g. 'WEBP', 'JPEG')
    :param quality: Quality/compression level (integer)
    :return: Django ContentFile ready to save or None if no input
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

    img = apply_exif_orientation(img)

    if img.width > max_size[0] or img.height > max_size[1]:
        # Заменяем Image.ANTIALIAS на Image.Resampling.LANCZOS
        # или просто опускаем второй аргумент
        img.thumbnail(max_size)

    supports_alpha = img_format in ('WEBP', 'PNG')
    
    if supports_alpha and img.mode in ('RGBA', 'LA'):
        mode = 'RGBA'
    else:
        mode = 'RGB'

    img = img.convert(mode)

    img.info.pop('exif', None)

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

    base, _ = image_field.name.rsplit('.', 1)
    prefix = f"{instance_id}_" if instance_id else ''
    unique_id = uuid.uuid4().hex[:8]
    new_name = f"{prefix}{base}_{unique_id}.{img_format.lower()}"

    return ContentFile(buffer.read(), name=new_name)
