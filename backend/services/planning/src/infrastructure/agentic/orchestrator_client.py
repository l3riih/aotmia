"""
Cliente para el Orquestador Agéntico
"""

import httpx
import structlog
from typing import Dict, Any, Optional
from utils.logger import get_logger
from utils.settings import get_settings

logger = get_logger(__name__)
settings = get_settings()


class OrchestratorClient:
    """Cliente para comunicarse con el servicio LLM Orchestrator"""
    
    def __init__(self, base_url: str, http_client: httpx.AsyncClient):
        self.base_url = base_url.rstrip("/")
        self.http_client = http_client
    
    async def process_educational_task(
        self, 
        task: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Procesa una tarea educativa con el agente.
        
        Args:
            task: Diccionario con la tarea educativa
            
        Returns:
            Respuesta del agente con razonamiento y resultado
        """
        try:
            url = f"{self.base_url}/agent/process"
            
            logger.info(
                "Sending task to orchestrator",
                task_type=task.get("task_type"),
                user_id=task.get("user_id")
            )
            
            response = await self.http_client.post(
                url,
                json=task,
                timeout=60.0  # Timeout extendido para tareas complejas
            )
            
            response.raise_for_status()
            result = response.json()
            
            logger.info(
                "Orchestrator response received",
                iterations=result.get("iterations"),
                confidence=result.get("confidence"),
                tools_used=len(result.get("tools_used", []))
            )
            
            return result
            
        except httpx.TimeoutException:
            logger.error("Orchestrator request timeout")
            raise Exception("Timeout al procesar tarea educativa")
            
        except httpx.HTTPStatusError as e:
            logger.error(
                "Orchestrator HTTP error",
                status_code=e.response.status_code,
                detail=e.response.text
            )
            raise Exception(f"Error del orquestador: {e.response.status_code}")
            
        except Exception as e:
            logger.error("Orchestrator request failed", error=str(e))
            raise
    
    async def health_check(self) -> bool:
        """Verifica la salud del orquestador"""
        try:
            response = await self.http_client.get(
                f"{self.base_url}/health",
                timeout=5.0
            )
            return response.status_code == 200
        except Exception:
            return False 