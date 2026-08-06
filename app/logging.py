import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
import os

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)


def setup_logger(name="app_logger", level=logging.DEBUG):
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if logger.handlers:
        return logger

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)

    file_handler = logging.FileHandler(f"{LOG_DIR}/app.log")
    file_handler.setLevel(logging.DEBUG)

    rotating_handler = RotatingFileHandler(
        f"{LOG_DIR}/app_rotating.log",
        maxBytes=1_000_000,
        backupCount=3
    )
    rotating_handler.setLevel(logging.DEBUG)

    timed_handler = TimedRotatingFileHandler(
        f"{LOG_DIR}/app_timed.log",
        when="midnight",
        interval=1,
        backupCount=7
    )
    timed_handler.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    rotating_handler.setFormatter(formatter)
    timed_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.addHandler(rotating_handler)
    logger.addHandler(timed_handler)

    return logger


logger = setup_logger()