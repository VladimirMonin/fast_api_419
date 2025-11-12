"""
Модуль для работы с загрузкой и хранением файлов.
Простое локальное хранилище для учебного проекта.
"""

import logging
import uuid
from pathlib import Path
from fastapi import UploadFile, HTTPException

logger = logging.getLogger(__name__)

# Директория для загрузки изображений
UPLOAD_DIR = Path("uploads/products")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Разрешённые расширения файлов
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}

# Максимальный размер файла (5 МБ)
MAX_FILE_SIZE = 5 * 1024 * 1024


async def save_product_image(file: UploadFile) -> str:
    """
    Сохраняет изображение товара и возвращает относительный URL.

    Args:
        file: Загруженный файл (UploadFile)

    Returns:
        str: Относительный URL к файлу (например: /uploads/products/abc123.jpg)

    Raises:
        HTTPException: При ошибках валидации или сохранения
    """
    logger.info(f"📥 Начало загрузки файла: {file.filename}")

    # Проверка наличия имени файла
    if not file.filename:
        logger.error("❌ Имя файла отсутствует")
        raise HTTPException(status_code=400, detail="Имя файла отсутствует")

    # Проверка расширения файла
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        logger.error(f"❌ Недопустимое расширение файла: {ext}")
        raise HTTPException(
            status_code=400,
            detail=f"Разрешены только изображения: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # Чтение содержимого файла
    content = await file.read()

    # Проверка размера файла
    file_size = len(content)
    if file_size > MAX_FILE_SIZE:
        logger.error(f"❌ Файл слишком большой: {file_size} байт")
        raise HTTPException(
            status_code=400,
            detail=f"Файл слишком большой. Максимум: {MAX_FILE_SIZE / (1024 * 1024):.1f} МБ",
        )

    # Генерация уникального имени файла
    filename = f"{uuid.uuid4()}{ext}"
    filepath = UPLOAD_DIR / filename

    # Сохранение файла
    try:
        with open(filepath, "wb") as f:
            f.write(content)
        logger.info(f"✅ Файл сохранён: {filename} ({file_size} байт)")
    except Exception as e:
        logger.error(f"❌ Ошибка при сохранении файла: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка сохранения файла: {e}")

    # Возвращаем относительный URL
    image_url = f"/uploads/products/{filename}"
    logger.info(f"✅ Изображение доступно по адресу: {image_url}")
    return image_url


def delete_product_image(image_url: str) -> bool:
    """
    Удаляет изображение товара из файловой системы.

    Args:
        image_url: Относительный URL изображения (например: /uploads/products/abc123.jpg)

    Returns:
        bool: True если файл удалён, False если не найден или ошибка
    """
    try:
        # Извлекаем имя файла из URL
        filename = Path(image_url).name
        filepath = UPLOAD_DIR / filename

        if filepath.exists():
            filepath.unlink()
            logger.info(f"🗑️ Удалено изображение: {filename}")
            return True
        else:
            logger.warning(f"⚠️ Файл не найден для удаления: {filename}")
            return False
    except Exception as e:
        logger.error(f"❌ Ошибка при удалении изображения: {e}")
        return False
