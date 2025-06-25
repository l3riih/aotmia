"""
Cliente para comunicación con el LLM Orchestrator Service.
Maneja las llamadas al agente educativo para evaluación de respuestas.
"""

import httpx
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
from ...core.config import get_settings
from ...core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class OrchestratorClient:
    """Cliente para comunicación con el servicio LLM Orchestrator."""
    
    def __init__(self):
        self.base_url = settings.LLM_ORCHESTRATOR_URL
        self.timeout = httpx.Timeout(timeout=60.0, connect=5.0)
        self.max_retries = 3
        self.retry_delay = 1.0
        
    async def process_educational_task(
        self,
        task_type: str,
        query: str,
        user_id: str,
        context: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Procesa una tarea educativa usando el agente.
        
        Args:
            task_type: Tipo de tarea (evaluate_response, generate_feedback, etc.)
            query: Consulta o prompt principal
            user_id: ID del usuario
            context: Contexto adicional para el agente
            metadata: Metadatos de la tarea
            
        Returns:
            Respuesta del agente con razonamiento y resultado
        """
        try:
            # Preparar el payload
            payload = {
                "task_type": task_type,
                "query": query,
                "user_id": user_id,
                "context": context or {},
                "metadata": metadata or {}
            }
            
            logger.info(
                "Enviando tarea educativa al orquestador",
                extra={
                    "task_type": task_type,
                    "user_id": user_id,
                    "context_keys": list(context.keys()) if context else []
                }
            )
            
            # Intentar con reintentos
            for attempt in range(self.max_retries):
                try:
                    async with httpx.AsyncClient(timeout=self.timeout) as client:
                        response = await client.post(
                            f"{self.base_url}/agent/process",
                            json=payload
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            
                            logger.info(
                                "Respuesta exitosa del orquestador",
                                extra={
                                    "task_type": task_type,
                                    "iterations": result.get("iterations", 0),
                                    "tools_used": result.get("tools_used", []),
                                    "reasoning_steps": len(result.get("reasoning_steps", []))
                                }
                            )
                            
                            return result
                            
                        elif response.status_code == 429:  # Rate limit
                            wait_time = int(response.headers.get("Retry-After", 5))
                            logger.warning(f"Rate limit alcanzado, esperando {wait_time}s")
                            await asyncio.sleep(wait_time)
                            continue
                            
                        else:
                            logger.error(
                                f"Error del orquestrador: {response.status_code}",
                                extra={"response_text": response.text}
                            )
                            
                except httpx.ConnectError:
                    logger.warning(
                        f"Error de conexión con orquestador (intento {attempt + 1}/{self.max_retries})"
                    )
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(self.retry_delay * (attempt + 1))
                        continue
                    else:
                        raise
                        
                except httpx.TimeoutException:
                    logger.warning(
                        f"Timeout en orquestador (intento {attempt + 1}/{self.max_retries})"
                    )
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(self.retry_delay * (attempt + 1))
                        continue
                    else:
                        raise
                        
        except Exception as e:
            logger.error(
                f"Error procesando tarea educativa: {str(e)}",
                extra={"task_type": task_type, "error_type": type(e).__name__}
            )
            
            # Retornar respuesta de fallback
            return {
                "answer": "Error al procesar la evaluación.",
                "reasoning_steps": [f"ERROR: {str(e)}"],
                "tools_used": [],
                "iterations": 0,
                "user_context": {},
                "final_answer": "No se pudo completar la evaluación debido a un error técnico.",
                "error": str(e)
            }
    
    async def search_memory(
        self,
        query: str,
        user_id: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Busca en la memoria semántica del agente.
        
        Args:
            query: Consulta de búsqueda
            user_id: ID del usuario (opcional)
            limit: Límite de resultados
            
        Returns:
            Lista de memorias relevantes
        """
        try:
            params = {
                "query": query,
                "limit": limit
            }
            if user_id:
                params["user_id"] = user_id
                
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/agent/memory/search",
                    params=params
                )
                
                if response.status_code == 200:
                    return response.json().get("results", [])
                else:
                    logger.error(f"Error buscando memoria: {response.status_code}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error en búsqueda de memoria: {str(e)}")
            return []
    
    async def get_user_context(self, user_id: str) -> Dict[str, Any]:
        """
        Obtiene el contexto completo de un usuario del agente.
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Contexto del usuario
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/agent/context/{user_id}"
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Error obteniendo contexto: {response.status_code}")
                    return {}
                    
        except Exception as e:
            logger.error(f"Error obteniendo contexto de usuario: {str(e)}")
            return {}
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Verifica el estado del servicio LLM Orchestrator.
        
        Returns:
            Estado del servicio
        """
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(timeout=5.0)) as client:
                response = await client.get(f"{self.base_url}/health")
                
                if response.status_code == 200:
                    return {
                        "status": "healthy",
                        "orchestrator_available": True,
                        "response": response.json()
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "orchestrator_available": False,
                        "error": f"Status code: {response.status_code}"
                    }
                    
        except Exception as e:
            return {
                "status": "unhealthy",
                "orchestrator_available": False,
                "error": str(e)
            }


# Instancia singleton
_orchestrator_client = None

def get_orchestrator_client() -> OrchestratorClient:
    """Obtiene la instancia singleton del cliente del orquestador."""
    global _orchestrator_client
    if _orchestrator_client is None:
        _orchestrator_client = OrchestratorClient()
    return _orchestrator_client 