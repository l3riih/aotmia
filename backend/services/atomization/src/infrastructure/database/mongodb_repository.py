"""
Repositorio MongoDB para átomos de aprendizaje
(Versión mock para pruebas)
"""

import structlog
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

logger = structlog.get_logger()


class MongoDBAtomRepository:
    """Repositorio MongoDB simulado para desarrollo y pruebas"""
    
    def __init__(self, mongodb_url: str, db_name: str):
        self.mongodb_url = mongodb_url
        self.db_name = db_name
        # Almacenamiento en memoria para pruebas
        self._atoms_storage: Dict[str, Dict[str, Any]] = {}
        logger.info("Initialized MongoDB repository (mock)", db_name=db_name)
    
    async def save_many_with_agent_metadata(
        self, 
        atoms: List[Any], 
        agent_metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Guarda múltiples átomos con metadatos del agente"""
        saved_atoms = []
        
        for atom in atoms:
            # Manejar tanto diccionarios como objetos
            if isinstance(atom, dict):
                # Es un diccionario
                atom_id = atom.get('id') or str(uuid.uuid4())
                atom_dict = {
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
            else:
                # Es un objeto (comportamiento original)
                atom_id = getattr(atom, 'id', None) or str(uuid.uuid4())
                atom_dict = {
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
            
            # Guardar en almacenamiento simulado
            self._atoms_storage[atom_id] = atom_dict
            saved_atoms.append(atom_dict)
            
            logger.info("Saved atom with agent metadata", 
                       atom_id=atom_id, 
                       title=atom_dict["title"],
                       reasoning_steps=len(agent_metadata.get("reasoning_steps", [])))
        
        return saved_atoms
    
    async def get(self, atom_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene un átomo por ID"""
        return self._atoms_storage.get(atom_id)
    
    async def get_all(self) -> List[Dict[str, Any]]:
        """Obtiene todos los átomos"""
        return list(self._atoms_storage.values())
    
    async def search_by_content(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Busca átomos por contenido (búsqueda simple)"""
        results = []
        query_lower = query.lower()
        
        for atom in self._atoms_storage.values():
            if (query_lower in atom["title"].lower() or 
                query_lower in atom["content"].lower() or
                any(query_lower in tag.lower() for tag in atom["tags"])):
                results.append(atom)
                
                if len(results) >= limit:
                    break
        
        return results 