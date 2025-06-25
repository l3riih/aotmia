"""
Servicio de atomización agéntica que usa el sistema de IA con razonamiento avanzado
"""

from typing import List, Optional, Dict, Any
import hashlib
import json
import re
from datetime import datetime
import structlog
from uuid import uuid4, UUID

from ...schemas import LearningAtomRead, AtomizationTaskRequest
from ...core.logging import log_agentic_operation

logger = structlog.get_logger()


class AgenticAtomizationService:
    """
    Servicio de atomización que usa el agente educativo con razonamiento avanzado.
    
    Integra con el sistema agéntico completo (llm_orchestrator) para ejecutar
    el workflow Plan-Execute-Observe-Reflect en la atomización de contenido.
    """
    
    def __init__(
        self,
        atom_repository,  # MongoDBAtomRepository
        agentic_orchestrator,  # AgenticOrchestratorClient  
        cache_service,  # RedisCacheService
        graph_repository  # Neo4jRepository
    ):
        self.atom_repository = atom_repository
        self.agent = agentic_orchestrator
        self.cache_service = cache_service
        self.graph_repository = graph_repository
    
    async def atomize_with_agent(
        self, 
        content: str, 
        objectives: str = "",
        difficulty: str = "intermedio",
        user_id: Optional[str] = None
    ) -> List[LearningAtomRead]:
        """
        Atomiza contenido usando el sistema agéntico completo.
        
        El agente ejecuta el workflow Plan-Execute-Observe-Reflect:
        1. PLAN: Analiza el contenido y planifica estrategia de atomización
        2. EXECUTE: Usa herramientas educativas para crear átomos
        3. OBSERVE: Valida la calidad pedagógica de los átomos
        4. REFLECT: Mejora los átomos basado en principios educativos
        """
        log_agentic_operation(
            logger,
            "atomization_start",
            user_id=user_id,
            content_length=len(content),
            difficulty=difficulty
        )
        
        # Verificar cache con contexto agéntico
        cache_key = self._generate_agentic_cache_key(content, objectives, difficulty, user_id)
        cached_result = await self.cache_service.get(cache_key)
        
        if cached_result:
            logger.info("Cache hit for atomization", cache_key=cache_key, user_id=user_id)
            return cached_result
        
        # Construir tarea educativa para el agente
        educational_task = self._build_educational_task(
            content, objectives, difficulty, user_id
        )
        
        # Procesar con agente usando workflow completo
        agent_result = await self.agent.process_educational_task(educational_task)
        
        # Extraer átomos de la respuesta agéntica
        atoms_data = self._extract_atoms_from_agent_response(agent_result)
        
        # --- FIX: Asegurar que el nivel de dificultad esté presente ---
        # El agente a veces puede omitir este campo, lo reinyectamos aquí
        # para asegurar la validación Pydantic.
        for atom in atoms_data:
            if 'difficulty_level' not in atom:
                atom['difficulty_level'] = difficulty
        # --- FIN DEL FIX ---

        if not atoms_data:
            logger.warning("No atoms extracted from agent response", user_id=user_id)
            atoms_data = self._create_fallback_atoms(content, difficulty)
        
        # Resolver dependencias entre átomos antes de validar
        resolved_atoms_data = self._resolve_atom_dependencies(atoms_data)
        
        # Validar y enriquecer con metadatos agénticos
        validated_atoms = await self._validate_and_enrich_atoms_agentic(
            resolved_atoms_data, 
            agent_result
        )
        
        # Guardar en base de datos con trazabilidad agéntica
        saved_atoms = await self.atom_repository.save_many_with_agent_metadata(
            validated_atoms,
            agent_metadata={
                "reasoning_steps": agent_result.get("reasoning_steps", []),
                "tools_used": agent_result.get("tools_used", []),
                "iterations": agent_result.get("iterations", 0),
                "quality_score": self._assess_reasoning_quality(agent_result)
            }
        )
        
        # Guardar relaciones en el grafo de conocimiento
        await self.graph_repository.save_atoms_with_relationships(saved_atoms)
        
        # Cachear resultado con contexto agéntico
        await self.cache_service.set(cache_key, saved_atoms, ttl=3600)
        
        log_agentic_operation(
            logger,
            "atomization_complete",
            user_id=user_id,
            atoms_created=len(saved_atoms),
            reasoning_steps=len(agent_result.get("reasoning_steps", []))
        )
        
        return saved_atoms
    
    def _build_educational_task(
        self, content: str, objectives: str, difficulty: str, user_id: Optional[str]
    ) -> Dict[str, Any]:
        """Construye la tarea educativa para el agente"""
        query = f"""
Atomiza el siguiente contenido educativo en unidades de aprendizaje coherentes y autocontenidas:

CONTENIDO A ATOMIZAR:
{content}

OBJETIVOS DE APRENDIZAJE:
{objectives or "No especificados"}

NIVEL DE DIFICULTAD:
{difficulty}

INSTRUCCIONES PEDAGÓGICAS:
- Aplica principios de microaprendizaje (Skinner): Divide en unidades pequeñas y autosuficientes.
- IDENTIFICA Y ESTABLECE PRERREQUISITOS: Por cada átomo, identifica si depende de otro átomo en el mismo lote. Usa el campo 'id_placeholder' para crear la relación.
- Cada átomo debe ser fácilmente evaluable.
- Mantén coherencia conceptual en cada átomo.
- Incluye objetivos de aprendizaje específicos.
- Estima tiempo de estudio para cada átomo.

FORMATO DE RESPUESTA:
Devuelve los átomos en formato JSON con la siguiente estructura. Es VITAL que cada átomo tenga un 'id_placeholder' único y que 'prerequisites' use esos placeholders.
```json
[
    {{
        "id_placeholder": "tema_1_unico",
        "title": "Título descriptivo del átomo 1",
        "content": "Contenido completo del átomo 1",
        "difficulty_level": "{difficulty}",
        "learning_objectives": ["objetivo1", "objetivo2"],
        "prerequisites": [],
        "estimated_time_minutes": 15,
        "tags": ["tag1", "tag2"]
    }},
    {{
        "id_placeholder": "tema_2_dependiente",
        "title": "Título descriptivo del átomo 2",
        "content": "Contenido completo del átomo 2 que depende del 1",
        "difficulty_level": "{difficulty}",
        "learning_objectives": ["objetivo3"],
        "prerequisites": ["tema_1_unica"],
        "estimated_time_minutes": 20,
        "tags": ["tag3"]
    }}
]
```
"""
        return {
            "query": query,
            "user_id": user_id,
            "task_type": "ATOMIZATION",
            "context": {
                "content_type": "educational_material",
                "objectives": objectives,
                "difficulty": difficulty,
                "content_length": len(content),
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    
    def _generate_agentic_cache_key(
        self, content: str, objectives: str, difficulty: str, user_id: Optional[str]
    ) -> str:
        """Genera clave de cache considerando contexto agéntico"""
        key_data = f"{content}:{objectives}:{difficulty}:{user_id or 'anonymous'}"
        hash_key = hashlib.md5(key_data.encode()).hexdigest()
        return f"agentic_atoms:{hash_key}"
    
    def _resolve_atom_dependencies(self, atoms_data: List[Dict]) -> List[Dict]:
        """
        Resuelve las dependencias de prerrequisitos entre átomos generados.

        El agente usa 'id_placeholder' para definir relaciones. Este método
        reemplaza esos placeholders con UUIDs reales antes de guardar.
        """
        if not atoms_data or not isinstance(atoms_data, list):
            return []

        placeholder_to_uuid_map = {
            atom.get("id_placeholder"): uuid4()
            for atom in atoms_data if atom.get("id_placeholder")
        }

        resolved_atoms = []
        for atom in atoms_data:
            atom_placeholder = atom.get("id_placeholder")
            if not atom_placeholder:
                # Si un átomo no tiene placeholder, no podemos procesarlo correctamente
                # con el resto, así que le asignamos un id para que no rompa el flujo.
                atom["id"] = uuid4()
                resolved_atoms.append(atom)
                continue
            
            atom["id"] = placeholder_to_uuid_map[atom_placeholder]
            
            raw_prerequisites = atom.get("prerequisites", [])
            if isinstance(raw_prerequisites, list):
                resolved_prerequisites = [
                    placeholder_to_uuid_map.get(p)
                    for p in raw_prerequisites if placeholder_to_uuid_map.get(p)
                ]
                atom["prerequisites"] = [str(uuid) for uuid in resolved_prerequisites if uuid] # Asegurar que sean strings
            else:
                atom["prerequisites"] = [] # Asegurar que siempre sea una lista
            
            resolved_atoms.append(atom)
            
        return resolved_atoms
    
    def _extract_atoms_from_agent_response(self, agent_result: Dict[str, Any]) -> List[Dict]:
        """Extrae átomos de la respuesta estructurada del agente"""
        try:
            answer = agent_result.get("answer", "")
            
            # Intentar parsear JSON si está presente
            json_pattern = r'```json\s*(.*?)\s*```'
            json_matches = re.findall(json_pattern, answer, re.DOTALL)
            
            for match in json_matches:
                try:
                    data = json.loads(match)
                    if isinstance(data, list) and data:
                        return data
                    elif isinstance(data, dict) and "atoms" in data:
                        return data["atoms"]
                except json.JSONDecodeError:
                    continue
            
            # Si no hay JSON, usar heurísticas para extraer átomos del texto
            return self._parse_atoms_from_text(answer)
            
        except Exception as e:
            logger.error("Error extracting atoms from agent response", error=str(e))
            return []
    
    def _parse_atoms_from_text(self, text: str) -> List[Dict]:
        """Parsea átomos de respuesta en texto libre usando heurísticas"""
        atoms = []
        
        # Buscar patrones tipo "Átomo 1:", "1.", etc.
        atom_pattern = r'(?:Átomo|Atom)\s*(\d+)[:\.]?\s*(.*?)(?=(?:Átomo|Atom)\s*\d+|$)'
        matches = re.findall(atom_pattern, text, re.DOTALL | re.IGNORECASE)
        
        for match in matches:
            atom_num, content_text = match
            if content_text.strip():
                # Extraer título de las primeras líneas
                lines = content_text.strip().split('\n')
                title = lines[0][:100] if lines else f"Átomo de Aprendizaje {atom_num}"
                
                atoms.append({
                    "title": title,
                    "content": content_text.strip(),
                    "difficulty_level": "intermedio",
                    "learning_objectives": [],
                    "prerequisites": [],
                    "estimated_time_minutes": 10,
                    "tags": []
                })
        
        return atoms
    
    def _create_fallback_atoms(self, content: str, difficulty: str) -> List[Dict]:
        """Crea átomos de fallback cuando el agente falla"""
        # Dividir contenido en párrafos como fallback básico
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        
        atoms = []
        for i, paragraph in enumerate(paragraphs[:5]):  # Máximo 5 átomos
            if len(paragraph) > 50:  # Solo párrafos suficientemente largos
                atoms.append({
                    "title": f"Concepto {i+1}: {paragraph[:50]}...",
                    "content": paragraph,
                    "difficulty_level": difficulty,
                    "learning_objectives": [],
                    "prerequisites": [],
                    "estimated_time_minutes": 10,
                    "tags": ["fallback"]
                })
        
        return atoms
    
    async def _validate_and_enrich_atoms_agentic(
        self, 
        atoms_data: List[Dict],
        agent_result: Dict[str, Any]
    ) -> List[Dict]:
        """Valida y enriquece átomos con metadatos agénticos adicionales"""
        validated = []
        
        for i, atom_data in enumerate(atoms_data):
            # Validar estructura básica
            if not self._is_valid_atom_structure(atom_data):
                logger.warning(f"Invalid atom structure at index {i}", atom_data=atom_data)
                continue
            
            # Enriquecer con metadatos agénticos
            atom_data.update({
                'created_at': datetime.utcnow(),
                'version': 1,
                'status': 'active',
                'created_by_agent': True,
                'agent_reasoning_quality': self._assess_reasoning_quality(agent_result),
                'tools_used_count': len(agent_result.get("tools_used", [])),
                'iteration_count': agent_result.get("iterations", 0)
            })
            
            validated.append(atom_data)
        
        logger.info(f"Validated {len(validated)} atoms from {len(atoms_data)} candidates")
        return validated
    
    def _is_valid_atom_structure(self, atom_data: Dict) -> bool:
        """Valida que un átomo tenga la estructura mínima requerida"""
        required_fields = ['title', 'content']
        return all(
            field in atom_data and 
            atom_data[field] and 
            isinstance(atom_data[field], str) and 
            len(atom_data[field].strip()) > 0
            for field in required_fields
        )
    
    def _assess_reasoning_quality(self, agent_result: Dict[str, Any]) -> float:
        """Evalúa la calidad del razonamiento del agente (0.0 a 1.0)"""
        reasoning_steps = agent_result.get("reasoning_steps", [])
        tools_used = agent_result.get("tools_used", [])
        iterations = agent_result.get("iterations", 0)
        
        # Heurística para evaluar calidad
        quality_score = 0.5  # Base
        
        # Más pasos de razonamiento = mejor calidad
        if len(reasoning_steps) >= 3:
            quality_score += 0.2
        
        # Uso de herramientas educativas = mejor calidad
        if len(tools_used) >= 2:
            quality_score += 0.2
        
        # Iteraciones controladas = mejor calidad
        if 1 <= iterations <= 5:
            quality_score += 0.1
        
        return min(1.0, quality_score)
    
    async def get_atom_by_id(self, atom_id: str) -> Optional[LearningAtomRead]:
        """Obtiene un átomo por ID"""
        try:
            return await self.atom_repository.get_by_id(atom_id)
        except Exception as e:
            logger.error("Error getting atom by ID", error=str(e), atom_id=atom_id)
            return None
    
    async def update_atom(self, atom_id: str, updates: Dict[str, Any]) -> Optional[LearningAtomRead]:
        """Actualiza un átomo existente"""
        try:
            return await self.atom_repository.update(atom_id, updates)
        except Exception as e:
            logger.error("Error updating atom", error=str(e), atom_id=atom_id)
            return None 