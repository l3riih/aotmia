"""
Configuración de logging para el servicio de autenticación
"""

import logging
import sys
import structlog
from typing import Any, Dict

def setup_logging(log_level: str = "INFO") -> None:
    """
    Configura el sistema de logging estructurado para el servicio de autenticación.
    """
    
    # Configurar logging estándar
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
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
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

def get_logger(name: str = __name__) -> Any:
    """
    Obtiene un logger estructurado para el componente especificado.
    """
    return structlog.get_logger(name) 