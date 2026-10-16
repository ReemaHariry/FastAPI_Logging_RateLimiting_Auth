import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from app.config import settings


def setup_logging() -> logging.Logger:
    """Configure application logging."""
    log_path = Path(settings.log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger()
    logger.setLevel(settings.log_level)
    if not logger.handlers:
        logging.basicConfig(
            level=settings.log_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                RotatingFileHandler(
                    settings.log_file,
                    maxBytes=settings.log_max_bytes,
                    backupCount=settings.log_backup_count,
                ),
                logging.StreamHandler(),
            ],
        )
    return logger
