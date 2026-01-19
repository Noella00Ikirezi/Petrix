"""Logging configuration with loguru."""

import sys
from pathlib import Path
from loguru import logger

from .settings import get_settings, get_logs_dir


def setup_logging() -> None:
    """Configure application logging."""
    settings = get_settings()
    logs_dir = get_logs_dir()

    # Remove default handler
    logger.remove()

    # Console handler
    logger.add(
        sys.stderr,
        level=settings.log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>",
        colorize=True,
    )

    # File handler
    log_file = logs_dir / "secop.log"
    logger.add(
        log_file,
        level="DEBUG" if settings.debug else settings.log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        rotation="10 MB",
        retention="30 days",
        compression="zip",
        encoding="utf-8",
    )

    # Audit log (security events)
    audit_log = logs_dir / "audit.log"
    logger.add(
        audit_log,
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
        rotation="50 MB",
        retention="1 year",
        compression="zip",
        encoding="utf-8",
        filter=lambda record: record["extra"].get("audit", False),
    )

    logger.info(f"Logging initialized - level: {settings.log_level}")


def get_audit_logger():
    """Get logger for audit events."""
    return logger.bind(audit=True)
