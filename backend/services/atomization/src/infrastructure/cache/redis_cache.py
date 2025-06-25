"""
Servicio de Cache Redis
(Versión mock para pruebas)
"""

import structlog
from typing import Any, Optional, Dict
import json
import time

logger = structlog.get_logger()


class RedisCacheService:
    """Servicio de cache Redis simulado para desarrollo y pruebas"""
    
    def __init__(self, redis_url: str, default_ttl: int = 3600):
        self.redis_url = redis_url
        self.default_ttl = default_ttl
        # Almacenamiento en memoria para pruebas
        self._cache_storage: Dict[str, Dict[str, Any]] = {}
        logger.info("Initialized Redis cache service (mock)", default_ttl=default_ttl)
    
    async def get(self, key: str) -> Optional[Any]:
        """Obtiene un valor del cache"""
        if key in self._cache_storage:
            cache_entry = self._cache_storage[key]
            
            # Verificar TTL
            if cache_entry["expires_at"] > time.time():
                logger.debug("Cache hit", key=key)
                return cache_entry["value"]
            else:
                # Expirado, eliminar
                del self._cache_storage[key]
                logger.debug("Cache expired", key=key)
        
        logger.debug("Cache miss", key=key)
        return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Almacena un valor en el cache"""
        if ttl is None:
            ttl = self.default_ttl
        
        expires_at = time.time() + ttl
        
        # Serializar el valor para simular comportamiento Redis
        try:
            serialized_value = json.loads(json.dumps(value, default=str))
        except (TypeError, ValueError):
            # Si no se puede serializar, almacenar como string
            serialized_value = str(value)
        
        self._cache_storage[key] = {
            "value": serialized_value,
            "expires_at": expires_at
        }
        
        logger.debug("Cache set", key=key, ttl=ttl)
    
    async def delete(self, key: str) -> bool:
        """Elimina un valor del cache"""
        if key in self._cache_storage:
            del self._cache_storage[key]
            logger.debug("Cache deleted", key=key)
            return True
        return False
    
    async def exists(self, key: str) -> bool:
        """Verifica si una clave existe en el cache"""
        if key in self._cache_storage:
            cache_entry = self._cache_storage[key]
            if cache_entry["expires_at"] > time.time():
                return True
            else:
                # Expirado, eliminar
                del self._cache_storage[key]
        return False
    
    async def clear(self) -> None:
        """Limpia todo el cache"""
        self._cache_storage.clear()
        logger.info("Cache cleared")
    
    def _cleanup_expired(self) -> None:
        """Limpia entradas expiradas (método interno)"""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self._cache_storage.items()
            if entry["expires_at"] <= current_time
        ]
        
        for key in expired_keys:
            del self._cache_storage[key]
        
        if expired_keys:
            logger.debug("Cleaned up expired cache entries", count=len(expired_keys)) 