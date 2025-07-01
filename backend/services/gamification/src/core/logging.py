"""
Configuración de logging estructurado para el servicio de gamificación
"""

import structlog
import logging
from typing import Any, Dict


def setup_logging():
    """Configura logging estructurado para el servicio"""
    
    # Configurar structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
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
    
    # Configurar logging estándar
    logging.basicConfig(
        format="%(message)s",
        stream=None,
        level=logging.INFO,
    )


def log_gamification_event(
    logger: structlog.BoundLogger,
    event_type: str,
    user_id: str,
    **kwargs: Any
) -> None:
    """
    Logger especializado para eventos de gamificación
    
    Args:
        logger: Logger estructurado
        event_type: Tipo de evento (achievement_unlocked, points_earned, etc.)
        user_id: ID del usuario
        **kwargs: Datos adicionales del evento
    """
    logger.info(
        "Gamification event",
        event_type=event_type,
        user_id=user_id,
        **kwargs
    )


def log_engagement_metric(
    logger: structlog.BoundLogger,
    metric_name: str,
    value: float,
    user_id: str,
    **context: Any
) -> None:
    """
    Logger para métricas de engagement
    
    Args:
        logger: Logger estructurado
        metric_name: Nombre de la métrica
        value: Valor de la métrica
        user_id: ID del usuario
        **context: Contexto adicional
    """
    logger.info(
        "Engagement metric",
        metric=metric_name,
        value=value,
        user_id=user_id,
        **context
    )


def log_achievement_unlock(
    logger: structlog.BoundLogger,
    user_id: str,
    achievement_id: str,
    achievement_type: str,
    points_awarded: int,
    **metadata: Any
) -> None:
    """
    Logger especializado para desbloqueo de logros
    """
    log_gamification_event(
        logger,
        "achievement_unlocked",
        user_id,
        achievement_id=achievement_id,
        achievement_type=achievement_type,
        points_awarded=points_awarded,
        **metadata
    )


def log_streak_event(
    logger: structlog.BoundLogger,
    user_id: str,
    streak_type: str,
    streak_count: int,
    action: str,  # started, continued, broken, milestone
    **metadata: Any
) -> None:
    """
    Logger para eventos de rachas
    """
    log_gamification_event(
        logger,
        "streak_event",
        user_id,
        streak_type=streak_type,
        streak_count=streak_count,
        action=action,
        **metadata
    )


def log_challenge_event(
    logger: structlog.BoundLogger,
    user_id: str,
    challenge_id: str,
    action: str,  # started, completed, failed, progressed
    progress: float = 0.0,
    **metadata: Any
) -> None:
    """
    Logger para eventos de desafíos
    """
    log_gamification_event(
        logger,
        "challenge_event",
        user_id,
        challenge_id=challenge_id,
        action=action,
        progress=progress,
        **metadata
    ) 