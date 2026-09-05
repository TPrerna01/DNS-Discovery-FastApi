import logging.config
import os
from pathlib import Path

LOG_DIR = os.path.join(Path(__file__).resolve().parent.parent.parent, "logs")

# how many days of rotated log files to keep before old ones get deleted automatically
LOG_RETENTION_DAYS = 30


def setup_logging():
    os.makedirs(LOG_DIR, exist_ok=True)

    log_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "std_out": {
                "format": "%(asctime)s %(levelname)s [%(name)s] %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "std_out",
                "level": "INFO",
            },
            "file": {
                "class": "logging.handlers.TimedRotatingFileHandler",
                "filename": os.path.join(LOG_DIR, "app.log"),
                "when": "midnight",
                "backupCount": LOG_RETENTION_DAYS,
                "formatter": "std_out",
                "level": "INFO",
            },
        },
        "root": {
            "handlers": ["console", "file"],
            "level": "INFO",
        },
    }

    logging.config.dictConfig(log_config)
