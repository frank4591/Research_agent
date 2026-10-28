# # Which research task was running when something failed?
# # Did the planner, researcher, or synthesizer fail?
# How long did each API operation take?
# How many research tasks succeeded or failed?
# Where should we look when a run produces an incomplete report?

# What this gives you
# - JSON logs that are easy to search and parse.
# - Console output for development.
# - A persistent logs/research_agent.log file.
# - Log rotation at approximately 5 MB, keeping three backups.
# - UTC timestamps and exception details when you log exceptions.

import logging
import json
import os
from datetime import datetime,timezone
from logging.handlers import RotatingFileHandler
from logging import FileHandler,StreamHandler
from pathlib import Path


class JSONFormatter(logging.Formatter):
    "format log records as one json object per line"
    def format(self, record:logging.LogRecord)->str:
        log_entry = {
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

         # Include additional structured fields supplied via `extra`.
        reserved = set(logging.makeLogRecord({}).__dict__)
        for key, value in record.__dict__.items():
            if key not in reserved and key not in {
                "message",
                "asctime",
            }:
                log_entry[key] = value

        if record.exc_info:
            log_entry["exception"] = self.formatException(
                record.exc_info
            )

        return json.dumps(log_entry, default=str)


def configure_logging() -> None:
    """Configure JSON logs for console and rotating log file."""

    log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, log_level, logging.INFO)

    formatter = JSONFormatter()

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    file_handler = RotatingFileHandler(
        log_dir / "research_agent.log",
        maxBytes=5_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Avoid duplicate handlers if configuration is called again.
    root_logger.handlers.clear()
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
