"""
Cliente para el servicio de evaluación
"""

import httpx
import structlog
from typing import Dict, Any, List

logger = structlog.get_logger(__name__)


class EvaluationClient:
    """Cliente para comunicarse con el servicio de evaluación"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
    
    async def get_user_evaluations(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Obtiene evaluaciones del usuario
        
        Args:
            user_id: ID del usuario
            limit: Límite de evaluaciones
            
        Returns:
            Lista de evaluaciones
        """
        # TODO: Implementar cliente real
        logger.info("Mock get evaluations", user_id=user_id, limit=limit)
        
        # Simulación de respuesta
        return [
            {
                "evaluation_id": f"eval_{user_id}_1",
                "user_id": user_id,
                "score": 0.8,
                "question_id": "q1",
                "feedback": {"message": "Bien hecho"},
                "created_at": "2024-01-01T10:00:00Z"
            }
        ] 