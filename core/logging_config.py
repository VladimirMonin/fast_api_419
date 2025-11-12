"""
Конфигурация логирования для приложения FastAPI.
Базовый логгер с выводом в консоль и файл.
"""

import logging
import logging.config
from pathlib import Path

# Директория для логов
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# Файл логов по умолчанию
DEFAULT_LOG_FILE = LOG_DIR / "app.log"


def setup_logging(
    log_level: str = "INFO", log_file: str | Path = DEFAULT_LOG_FILE
) -> None:
    """
    Настройка логирования для приложения.

    Args:
        log_level: Уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Путь к файлу логов
    """
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "standard",
                "stream": "ext://sys.stdout",
            },
            "file": {
                "class": "logging.FileHandler",
                "level": log_level,
                "formatter": "standard",
                "filename": str(log_file),
                "encoding": "utf-8",
                "mode": "a",  # append mode
            },
        },
        "loggers": {
            "": {  # root logger
                "handlers": ["console", "file"],
                "level": log_level,
                "propagate": False,
            },
            "uvicorn": {
                "handlers": ["console", "file"],
                "level": log_level,
                "propagate": False,
            },
            "uvicorn.error": {
                "handlers": ["console", "file"],
                "level": log_level,
                "propagate": False,
            },
            "uvicorn.access": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
        },
    }

    logging.config.dictConfig(config)
    logger = logging.getLogger(__name__)
    logger.info(f"Логирование настроено. Уровень: {log_level}, Файл: {log_file}")
