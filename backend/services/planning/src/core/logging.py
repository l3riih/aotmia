"""
Configuración de logging estructurado para el servicio de planificación
"""

import logging
import sys
import structlog
from pythonjsonlogger import jsonlogger

from .config import settings


def setup_logging():
    """Configura logging estructurado con structlog"""
    
    # Configurar el nivel de log
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    
    # Configurar formato según settings
    if settings.LOG_FORMAT == "json":
        # Configurar JSON logging
        logHandler = logging.StreamHandler(sys.stdout)
        formatter = jsonlogger.JsonFormatter(
            fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        logHandler.setFormatter(formatter)
        logging.root.addHandler(logHandler)
        logging.root.setLevel(log_level)
    else:
        # Configurar logging tradicional
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
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
            structlog.processors.dict_tracebacks,
            add_service_context,
            structlog.processors.JSONRenderer() if settings.LOG_FORMAT == "json" 
            else structlog.dev.ConsoleRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Silenciar logs excesivos de librerías externas
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def add_service_context(logger, log_method, event_dict):
    """Agrega contexto del servicio a todos los logs"""
    event_dict["service"] = settings.SERVICE_NAME
    event_dict["version"] = settings.SERVICE_VERSION
    event_dict["environment"] = "development"  # TODO: Obtener de env
    
    # Agregar contexto agéntico si está presente
    if "task_type" in event_dict:
        event_dict["agentic_context"] = {
            "task_type": event_dict.get("task_type"),
            "iterations": event_dict.get("iterations"),
            "confidence": event_dict.get("confidence")
        }
    
    # Agregar métricas de planificación si están presentes
    if "plan_id" in event_dict:
        event_dict["planning_context"] = {
            "plan_id": event_dict.get("plan_id"),
            "total_atoms": event_dict.get("total_atoms"),
            "estimated_days": event_dict.get("estimated_days")
        }
    
    return event_dict


def get_logger(name: str = None):
    """Obtiene un logger configurado"""
    return structlog.get_logger(name)


# Logger para métricas agénticas
class AgenticMetricsLogger:
    """Logger especializado para métricas agénticas"""
    
    def __init__(self):
        self.logger = get_logger("agentic_metrics")
    
    def log_planning_task(
        self,
        user_id: str,
        task_type: str,
        goals: list,
        duration_ms: int,
        iterations: int,
        confidence: float,
        success: bool
    ):
        """Log métricas de tarea de planificación"""
        self.logger.info(
            "Planning task completed",
            user_id=user_id,
            task_type=task_type,
            goals_count=len(goals),
            duration_ms=duration_ms,
            iterations=iterations,
            confidence=confidence,
            success=success,
            metric_type="planning_task"
        )
    
    def log_algorithm_usage(
        self,
        algorithm: str,
        input_size: int,
        processing_time_ms: int,
        output_quality: float
    ):
        """Log uso de algoritmos pedagógicos"""
        self.logger.info(
            "Algorithm executed",
            algorithm=algorithm,
            input_size=input_size,
            processing_time_ms=processing_time_ms,
            output_quality=output_quality,
            metric_type="algorithm_usage"
        )
    
    def log_adaptation(
        self,
        plan_id: str,
        adaptation_type: str,
        changes_count: int,
        reason: str,
        confidence: float
    ):
        """Log adaptaciones de planes"""
        self.logger.info(
            "Plan adapted",
            plan_id=plan_id,
            adaptation_type=adaptation_type,
            changes_count=changes_count,
            reason=reason,
            confidence=confidence,
            metric_type="plan_adaptation"
        )
    
    def log_recommendation(
        self,
        user_id: str,
        context: str,
        recommendations_count: int,
        avg_priority: float,
        response_time_ms: int
    ):
        """Log generación de recomendaciones"""
        self.logger.info(
            "Recommendations generated",
            user_id=user_id,
            context=context,
            recommendations_count=recommendations_count,
            avg_priority=avg_priority,
            response_time_ms=response_time_ms,
            metric_type="recommendations"
        )


# Instancia global del logger de métricas
agentic_metrics = AgenticMetricsLogger() 