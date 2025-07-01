"""
Cliente para el servicio de atomización
"""

import httpx
import structlog
from typing import Dict, Any, List

logger = structlog.get_logger(__name__)


class AtomizationClient:
    """Cliente para comunicarse con el servicio de atomización"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
    
    async def atomize_content(self, content: str, topic: str) -> List[Dict[str, Any]]:
        """
        Atomiza contenido en átomos de aprendizaje
        
        Args:
            content: Contenido a atomizar
            topic: Tópico principal
            
        Returns:
            Lista de átomos de aprendizaje
        """
        # TODO: Implementar cliente real
        logger.info("Mock atomization", topic=topic, content_length=len(content))
        
        # Simulación de respuesta
        return [
            {
                "id": f"atom_{topic.lower()}_1",
                "title": f"Introducción a {topic}",
                "content": content[:100] + "...",
                "difficulty": "básico",
                "dependencies": []
            }
        ] 