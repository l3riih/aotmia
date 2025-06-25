"""
Configuración de logging estructurado para el servicio de atomización
"""

import logging
import structlog
from typing import Any, Dict, Optional


def setup_logging() -> None:
    """Configura logging estructurado con structlog"""
    
    # Configurar logging estándar
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s"
    )
    
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
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: Optional[str] = None) -> structlog.BoundLogger:
    """Obtiene un logger estructurado"""
    return structlog.get_logger(name or __name__)


def log_agentic_operation(
    logger: structlog.BoundLogger,
    operation: str,
    user_id: Optional[str] = None,
    **kwargs: Any
) -> None:
    """Log helper for agentic operations"""
    logger.info(
        f"Agentic operation: {operation}",
        operation=operation,
        user_id=user_id,
        service="atomization",
        **kwargs
    ) 