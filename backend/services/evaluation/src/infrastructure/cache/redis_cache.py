"""
Servicio de cache con Redis para evaluaciones.
Almacena temporalmente resultados de evaluaciones frecuentes.
"""

import redis.asyncio as redis
import json
import hashlib
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import logging
from ...core.config import get_settings
from ...core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class RedisCache:
    """Servicio de cache con Redis para evaluaciones."""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.ttl_seconds = settings.REDIS_TTL_SECONDS
        self.enabled = settings.ENABLE_CACHE
        
    async def initialize(self):
        """Inicializa la conexión con Redis."""
        if not self.enabled:
            logger.info("Cache deshabilitado por configuración")
            return
            
        try:
            # Conectar a Redis
            self.redis_client = redis.Redis(
                host="localhost",  # TODO: Usar settings.REDIS_HOST cuando esté configurado
                port=6379,
                db=0,
                decode_responses=True
            )
            
            # Verificar conexión
            await self.redis_client.ping()
            logger.info("Conexión con Redis establecida correctamente")
            
        except Exception as e:
            logger.warning(f"No se pudo conectar a Redis: {str(e)}. Cache deshabilitado.")
            self.enabled = False
            self.redis_client = None
    
    def _generate_cache_key(self, prefix: str, data: Dict[str, Any]) -> str:
        """
        Genera una clave única para el cache.
        
        Args:
            prefix: Prefijo para la clave
            data: Datos para generar hash
            
        Returns:
            Clave de cache
        """
        # Crear hash de los datos
        data_str = json.dumps(data, sort_keys=True)
        data_hash = hashlib.md5(data_str.encode()).hexdigest()
        
        return f"{prefix}:{data_hash}"
    
    async def get_evaluation_cache(
        self,
        question_id: str,
        student_answer: str,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Busca una evaluación en cache.
        
        Args:
            question_id: ID de la pregunta
            student_answer: Respuesta del estudiante
            user_id: ID del usuario
            
        Returns:
            Evaluación cacheada o None
        """
        if not self.enabled or not self.redis_client:
            return None
            
        try:
            # Generar clave de cache
            cache_data = {
                "question_id": question_id,
                "answer_hash": hashlib.md5(student_answer.encode()).hexdigest(),
                "user_id": user_id
            }
            cache_key = self._generate_cache_key("eval", cache_data)
            
            # Buscar en cache
            cached_value = await self.redis_client.get(cache_key)
            
            if cached_value:
                logger.info(
                    "Evaluación encontrada en cache",
                    extra={
                        "cache_key": cache_key,
                        "user_id": user_id
                    }
                )
                return json.loads(cached_value)
                
            return None
            
        except Exception as e:
            logger.error(f"Error leyendo cache: {str(e)}")
            return None
    
    async def set_evaluation_cache(
        self,
        question_id: str,
        student_answer: str,
        user_id: str,
        evaluation_result: Dict[str, Any]
    ):
        """
        Almacena una evaluación en cache.
        
        Args:
            question_id: ID de la pregunta
            student_answer: Respuesta del estudiante
            user_id: ID del usuario
            evaluation_result: Resultado de la evaluación
        """
        if not self.enabled or not self.redis_client:
            return
            
        try:
            # Generar clave de cache
            cache_data = {
                "question_id": question_id,
                "answer_hash": hashlib.md5(student_answer.encode()).hexdigest(),
                "user_id": user_id
            }
            cache_key = self._generate_cache_key("eval", cache_data)
            
            # Almacenar en cache con TTL
            await self.redis_client.setex(
                cache_key,
                self.ttl_seconds,
                json.dumps(evaluation_result)
            )
            
            logger.info(
                "Evaluación almacenada en cache",
                extra={
                    "cache_key": cache_key,
                    "ttl_seconds": self.ttl_seconds,
                    "user_id": user_id
                }
            )
            
        except Exception as e:
            logger.error(f"Error escribiendo cache: {str(e)}")
    
    async def get_user_statistics_cache(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Busca estadísticas de usuario en cache.
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Estadísticas cacheadas o None
        """
        if not self.enabled or not self.redis_client:
            return None
            
        try:
            cache_key = f"user_stats:{user_id}"
            cached_value = await self.redis_client.get(cache_key)
            
            if cached_value:
                logger.info(f"Estadísticas encontradas en cache para usuario {user_id}")
                return json.loads(cached_value)
                
            return None
            
        except Exception as e:
            logger.error(f"Error leyendo estadísticas de cache: {str(e)}")
            return None
    
    async def set_user_statistics_cache(
        self,
        user_id: str,
        statistics: Dict[str, Any],
        ttl_seconds: Optional[int] = None
    ):
        """
        Almacena estadísticas de usuario en cache.
        
        Args:
            user_id: ID del usuario
            statistics: Estadísticas a cachear
            ttl_seconds: TTL personalizado (opcional)
        """
        if not self.enabled or not self.redis_client:
            return
            
        try:
            cache_key = f"user_stats:{user_id}"
            ttl = ttl_seconds or self.ttl_seconds
            
            await self.redis_client.setex(
                cache_key,
                ttl,
                json.dumps(statistics)
            )
            
            logger.info(f"Estadísticas almacenadas en cache para usuario {user_id}")
            
        except Exception as e:
            logger.error(f"Error escribiendo estadísticas en cache: {str(e)}")
    
    async def invalidate_user_cache(self, user_id: str):
        """
        Invalida todo el cache de un usuario.
        
        Args:
            user_id: ID del usuario
        """
        if not self.enabled or not self.redis_client:
            return
            
        try:
            # Buscar todas las claves del usuario
            pattern = f"*:{user_id}*"
            cursor = 0
            
            while True:
                cursor, keys = await self.redis_client.scan(
                    cursor,
                    match=pattern,
                    count=100
                )
                
                if keys:
                    await self.redis_client.delete(*keys)
                    
                if cursor == 0:
                    break
                    
            # También invalidar estadísticas
            await self.redis_client.delete(f"user_stats:{user_id}")
            
            logger.info(f"Cache invalidado para usuario {user_id}")
            
        except Exception as e:
            logger.error(f"Error invalidando cache: {str(e)}")
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del cache.
        
        Returns:
            Estadísticas del cache
        """
        if not self.enabled or not self.redis_client:
            return {"enabled": False}
            
        try:
            info = await self.redis_client.info()
            
            return {
                "enabled": True,
                "connected": True,
                "used_memory": info.get("used_memory_human", "N/A"),
                "connected_clients": info.get("connected_clients", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace": info.get("db0", {})
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas de cache: {str(e)}")
            return {
                "enabled": True,
                "connected": False,
                "error": str(e)
            }
    
    async def close(self):
        """Cierra la conexión con Redis."""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Conexión con Redis cerrada")

    async def get(self, key: str):
        """Obtiene un valor genérico del cache y lo deserializa si es JSON"""
        if not self.enabled or not self.redis_client:
            return None
        try:
            value = await self.redis_client.get(key)
            if value is None:
                return None
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        except Exception as e:
            logger.error("Error en RedisCache.get", error=str(e))
            return None

    async def set(self, key: str, value, ttl: Optional[int] = None):
        """Establece un valor genérico en el cache, serializando a JSON cuando corresponde"""
        if not self.enabled or not self.redis_client:
            return
        try:
            if isinstance(value, (dict, list)):
                serialized = json.dumps(value)
            else:
                serialized = str(value)
            await self.redis_client.setex(key, ttl or self.ttl_seconds, serialized)
        except Exception as e:
            logger.error("Error en RedisCache.set", error=str(e))


# Instancia singleton
_redis_cache = None

async def get_redis_cache() -> RedisCache:
    """Obtiene la instancia singleton del cache Redis."""
    global _redis_cache
    if _redis_cache is None:
        _redis_cache = RedisCache()
        await _redis_cache.initialize()
    return _redis_cache 