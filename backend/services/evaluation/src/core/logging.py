"""
Configuración de logging estructurado agéntico
"""

import logging
import sys
import structlog

try:
    from pythonjsonlogger import jsonlogger
except ImportError:
    jsonlogger = None

from .config import settings


def configure_logging():
    """Configura logging estructurado para el servicio"""
    
    # Configurar nivel de logging
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    
    # Configurar handler según formato
    if settings.LOG_FORMAT == "json":
        # JSON logging para producción
        handler = logging.StreamHandler(sys.stdout)
        formatter = jsonlogger.JsonFormatter(
            fmt="%(timestamp)s %(level)s %(name)s %(message)s",
            rename_fields={
                "timestamp": "timestamp",
                "level": "level",
                "name": "logger"
            }
        )
        handler.setFormatter(formatter)
    else:
        # Console logging para desarrollo
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
    
    # Configurar root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers = [handler]
    
    # Configurar structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer() if settings.LOG_FORMAT == "json" 
            else structlog.dev.ConsoleRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def log_agentic_operation(
    operation: str,
    user_id: str,
    service: str = "evaluation",
    **kwargs
):
    """Log helper para operaciones agénticas"""
    logger = structlog.get_logger()
    logger.info(
        f"Agentic operation: {operation}",
        operation=operation,
        user_id=user_id,
        service=service,
        **kwargs
    )


def log_agentic_error(
    operation: str,
    error: str,
    user_id: str,
    service: str = "evaluation",
    **kwargs
):
    """Log helper para errores agénticos"""
    logger = structlog.get_logger()
    logger.error(
        f"Agentic operation failed: {operation}",
        operation=operation,
        error=error,
        user_id=user_id,
        service=service,
        **kwargs
    )


def get_logger(name: str = None):
    """Obtiene un logger estructurado"""
    return structlog.get_logger(name)