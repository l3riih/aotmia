"""
Repositorio MongoDB para átomos de aprendizaje
"""

import structlog
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from pymongo.errors import DuplicateKeyError, ConnectionFailure

from ...schemas import LearningAtomRead, AgenticAtomizationResponse

logger = structlog.get_logger()


class MongoDBAtomRepository:
    """Repositorio MongoDB para átomos de aprendizaje"""
    
    def __init__(self, mongodb_url: str, db_name: str = "atomia_atoms"):
        self.mongodb_url = mongodb_url
        self.db_name = db_name
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None
        self.atoms_collection: Optional[AsyncIOMotorCollection] = None
        
        # Crear conexión asíncrona
        self._init_task = asyncio.create_task(self._initialize_connection())
        logger.info("MongoDB repository initialized", db_name=db_name, url=mongodb_url)
    
    async def _initialize_connection(self):
        """Inicializa la conexión a MongoDB"""
        try:
            self.client = AsyncIOMotorClient(self.mongodb_url)
            self.db = self.client[self.db_name]
            self.atoms_collection = self.db["learning_atoms"]
            
            # Verificar conexión
            await self.client.admin.command('ping')
            
            # Crear índices para mejorar rendimiento
            await self._create_indexes()
            
            logger.info("MongoDB connection established", db_name=self.db_name)
            
        except ConnectionFailure as e:
            logger.error("Failed to connect to MongoDB", error=str(e))
            raise
    
    async def _create_indexes(self):
        """Crea índices para optimizar consultas"""
        await self.atoms_collection.create_index("id", unique=True)
        await self.atoms_collection.create_index("title")
        await self.atoms_collection.create_index("tags")
        await self.atoms_collection.create_index("difficulty_level")
        await self.atoms_collection.create_index("created_at")
        await self.atoms_collection.create_index([("title", "text"), ("content", "text")])
        logger.info("MongoDB indexes created")
    
    async def save_many_with_agent_metadata(
        self, 
        atoms: List[Any], 
        agent_metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Guarda múltiples átomos con metadatos del agente"""
        await self._init_task
        
        saved_atoms = []
        
        for atom in atoms:
            # Manejar tanto diccionarios como objetos
            if isinstance(atom, dict):
                atom_dict = self._prepare_atom_dict_from_dict(atom, agent_metadata)
            else:
                atom_dict = self._prepare_atom_dict_from_object(atom, agent_metadata)
            
            try:
                # Insertar en MongoDB
                result = await self.atoms_collection.insert_one(atom_dict)
                atom_dict["_id"] = str(result.inserted_id)
                saved_atoms.append(atom_dict)
                
                logger.info("Saved atom with agent metadata", 
                           atom_id=atom_dict["id"], 
                           title=atom_dict["title"],
                           reasoning_steps=len(agent_metadata.get("reasoning_steps", [])))
                           
            except DuplicateKeyError:
                # Si ya existe, actualizar
                await self.atoms_collection.replace_one(
                    {"id": atom_dict["id"]}, 
                    atom_dict, 
                    upsert=True
                )
                saved_atoms.append(atom_dict)
                logger.info("Updated existing atom", atom_id=atom_dict["id"])
        
        return saved_atoms
    
    def _prepare_atom_dict_from_dict(self, atom: Dict[str, Any], agent_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Prepara diccionario de átomo desde un dict"""
        atom_id = atom.get('id') or str(uuid.uuid4())
        return {
            "id": atom_id,
            "title": atom.get('title', 'Sin título'),
            "content": atom.get('content', ''),
            "difficulty_level": atom.get('difficulty_level', atom.get('difficulty', 'intermedio')),
            "prerequisites": atom.get('prerequisites', []),
            "learning_objectives": atom.get('learning_objectives', []),
            "estimated_time_minutes": atom.get('estimated_time_minutes', 10),
            "tags": atom.get('tags', []),
            "created_at": atom.get('created_at', datetime.now()),
            "version": atom.get('version', 1),
            "status": atom.get('status', 'active'),
            "created_by_agent": atom.get('created_by_agent', True),
            # Metadatos agénticos
            "agent_reasoning_quality": atom.get('agent_reasoning_quality', 0.0),
            "tools_used_count": atom.get('tools_used_count', 0),
            "iteration_count": atom.get('iteration_count', 0),
            "agent_metadata": agent_metadata
        }
    
    def _prepare_atom_dict_from_object(self, atom: Any, agent_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Prepara diccionario de átomo desde un objeto"""
        atom_id = getattr(atom, 'id', None) or str(uuid.uuid4())
        return {
            "id": atom_id,
            "title": getattr(atom, 'title', 'Sin título'),
            "content": getattr(atom, 'content', ''),
            "difficulty_level": getattr(atom, 'difficulty_level', getattr(atom, 'difficulty', 'intermedio')),
            "prerequisites": getattr(atom, 'prerequisites', []) or [],
            "learning_objectives": getattr(atom, 'learning_objectives', []) or [],
            "estimated_time_minutes": getattr(atom, 'estimated_time_minutes', 10),
            "tags": getattr(atom, 'tags', []) or [],
            "created_at": getattr(atom, 'created_at', datetime.now()),
            "version": getattr(atom, 'version', 1),
            "status": getattr(atom, 'status', 'active'),
            "created_by_agent": getattr(atom, 'created_by_agent', True),
            # Metadatos agénticos
            "agent_reasoning_quality": getattr(atom, 'agent_reasoning_quality', 0.0),
            "tools_used_count": getattr(atom, 'tools_used_count', 0),
            "iteration_count": getattr(atom, 'iteration_count', 0),
            "agent_metadata": agent_metadata
        }
    
    async def get(self, atom_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene un átomo por ID"""
        await self._init_task
        
        result = await self.atoms_collection.find_one({"id": atom_id})
        if result:
            result["_id"] = str(result["_id"])  # Convertir ObjectId a string
        return result
    
    async def get_all(self, limit: int = 100, skip: int = 0) -> List[Dict[str, Any]]:
        """Obtiene todos los átomos con paginación"""
        await self._init_task
        
        cursor = self.atoms_collection.find().skip(skip).limit(limit)
        atoms = []
        async for atom in cursor:
            atom["_id"] = str(atom["_id"])
            atoms.append(atom)
        
        return atoms
    
    async def search_by_content(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Busca átomos por contenido usando índice de texto"""
        await self._init_task
        
        # Buscar usando el índice de texto de MongoDB
        cursor = self.atoms_collection.find(
            {"$text": {"$search": query}},
            {"score": {"$meta": "textScore"}}
        ).sort([("score", {"$meta": "textScore"})]).limit(limit)
        
        atoms = []
        async for atom in cursor:
            atom["_id"] = str(atom["_id"])
            atoms.append(atom)
        
        # Si no hay resultados con búsqueda de texto, usar búsqueda por regex
        if not atoms:
            cursor = self.atoms_collection.find({
                "$or": [
                    {"title": {"$regex": query, "$options": "i"}},
                    {"content": {"$regex": query, "$options": "i"}},
                    {"tags": {"$regex": query, "$options": "i"}}
                ]
            }).limit(limit)
            
            async for atom in cursor:
                atom["_id"] = str(atom["_id"])
                atoms.append(atom)
        
        return atoms
    
    async def get_by_difficulty(self, difficulty: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Obtiene átomos por nivel de dificultad"""
        await self._init_task
        
        cursor = self.atoms_collection.find({"difficulty_level": difficulty}).limit(limit)
        atoms = []
        async for atom in cursor:
            atom["_id"] = str(atom["_id"])
            atoms.append(atom)
        
        return atoms
    
    async def get_by_tags(self, tags: List[str], limit: int = 20) -> List[Dict[str, Any]]:
        """Obtiene átomos que contengan cualquiera de los tags especificados"""
        await self._init_task
        
        cursor = self.atoms_collection.find({"tags": {"$in": tags}}).limit(limit)
        atoms = []
        async for atom in cursor:
            atom["_id"] = str(atom["_id"])
            atoms.append(atom)
        
        return atoms
    
    async def update_atom(self, atom_id: str, update_data: Dict[str, Any]) -> bool:
        """Actualiza un átomo existente"""
        await self._init_task
        
        update_data["updated_at"] = datetime.now()
        result = await self.atoms_collection.update_one(
            {"id": atom_id},
            {"$set": update_data}
        )
        
        return result.modified_count > 0
    
    async def delete_atom(self, atom_id: str) -> bool:
        """Elimina un átomo"""
        await self._init_task
        
        result = await self.atoms_collection.delete_one({"id": atom_id})
        return result.deleted_count > 0
    
    async def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de la colección de átomos"""
        await self._init_task
        
        total_atoms = await self.atoms_collection.count_documents({})
        
        # Contar por dificultad
        difficulty_pipeline = [
            {"$group": {"_id": "$difficulty_level", "count": {"$sum": 1}}}
        ]
        difficulty_stats = {}
        async for doc in self.atoms_collection.aggregate(difficulty_pipeline):
            difficulty_stats[doc["_id"]] = doc["count"]
        
        # Contar átomos creados por agente
        agent_created = await self.atoms_collection.count_documents({"created_by_agent": True})
        
        return {
            "total_atoms": total_atoms,
            "difficulty_distribution": difficulty_stats,
            "agent_created_atoms": agent_created,
            "manual_created_atoms": total_atoms - agent_created
        }
    
    async def close(self):
        """Cierra la conexión a MongoDB"""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed") 