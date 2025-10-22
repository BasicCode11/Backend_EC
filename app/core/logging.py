
import logging
import sys
from loguru import logger
from app.core.config import settings

logger.remove()

#log format
log_format = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
    "<level>{message}</level>"
)

# Console logging
logger.add(
    sys.stdout,
    format=log_format,
    level=settings.LOG_LEVEL if hasattr(settings, "LOG_LEVEL") else "INFO",
    backtrace=True,   # show traceback
    diagnose=True     # show variables in stack trace
)

# Optional: log to file
logger.add(
    "logs/app.log",
    rotation="10 MB",    # Rotate after 10 MB
    retention="14 days", # Keep logs for 14 days
    compression="zip",   # Compress old logs
    level="DEBUG"
)

# Bridge standard logging → loguru
class InterceptHandler(logging.Handler):
    def emit(self, record):
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        logger.opt(depth=6, exception=record.exc_info).log(level, record.getMessage())

logging.basicConfig(handlers=[InterceptHandler()], level=0)

# Optional: function to get logger instance
def get_logger(name: str = "app"):
    return logger.bind(name=name)