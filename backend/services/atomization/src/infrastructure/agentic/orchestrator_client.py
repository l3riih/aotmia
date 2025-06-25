"""
Cliente para el Orquestrador Agéntico (LLM Orchestrator)
"""

import httpx
import structlog
from typing import Dict, Any, Optional

logger = structlog.get_logger(__name__)


class OrchestratorClient:
    """Cliente para comunicarse con el servicio LLM Orchestrator"""
    
    def __init__(self, base_url: str, timeout: int = 30, max_retries: int = 3):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.max_retries = max_retries
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=timeout
        )
    
    async def process_educational_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa una tarea educativa usando el agente de IA
        
        Args:
            task_data: Datos de la tarea incluyendo query, user_id, task_type, context
            
        Returns:
            Dict con la respuesta del agente incluyendo answer, reasoning_steps, tools_used, etc.
        """
        endpoint = "/agent/process"
        
        logger.info("Sending task to agentic orchestrator", 
                   task_type=task_data.get("task_type", "unknown"),
                   user_id=task_data.get("user_id", "anonymous"))
        
        try:
            response = await self._client.post(endpoint, json=task_data)
            response.raise_for_status()
            
            result = response.json()
            logger.info("Task completed successfully", 
                       iterations=result.get("iterations", 0),
                       tools_used_count=len(result.get("tools_used", [])))
            
            return result
            
        except httpx.HTTPStatusError as e:
            logger.error("HTTP error from orchestrator", 
                        status_code=e.response.status_code,
                        response_text=e.response.text)
            raise Exception(f"Orchestrator HTTP error: {e.response.status_code}")
            
        except httpx.RequestError as e:
            logger.error("Request error to orchestrator", error=str(e))
            raise Exception(f"Orchestrator connection error: {str(e)}")
    
    async def search_memory(self, query: str, user_id: Optional[str] = None, limit: int = 5) -> Dict[str, Any]:
        """Busca en la memoria semántica del agente"""
        endpoint = "/agent/memory/search"
        params = {"query": query, "limit": limit}
        if user_id:
            params["user_id"] = user_id
        
        try:
            response = await self._client.post(endpoint, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error("Memory search error", error=str(e))
            return {"results": []}
    
    async def get_user_context(self, user_id: str) -> Dict[str, Any]:
        """Obtiene el contexto completo de un usuario"""
        endpoint = f"/agent/context/{user_id}"
        
        try:
            response = await self._client.get(endpoint)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error("Context retrieval error", error=str(e))
            return {"error": str(e)}
    
    async def close(self):
        """Cierra el cliente HTTP"""
        await self._client.aclose() 