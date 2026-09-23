
import logging
import sys
from typing import Any


def configure_logging() -> logging.Logger:
    logger = logging.getLogger("feedback_watch_tower")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
        )
        logger.addHandler(handler)

    return logger


logger = configure_logging()


def log_context(**kwargs: Any) -> dict[str, Any]:
    return {str(key): value for key, value in kwargs.items()}
