"""
Repositorio completo de Neo4j para el Grafo de Conocimiento Agéntico de Atomia.
Maneja átomos de aprendizaje, relaciones, progreso de usuarios, y rutas adaptativas.
"""

from typing import List, Dict, Any, Optional, Tuple
from neo4j import GraphDatabase, Session
import structlog
import asyncio
from datetime import datetime
import uuid
import json

logger = structlog.get_logger()

class Neo4jKnowledgeGraph:
    """
    Repositorio agéntico para el grafo de conocimiento educativo.
    
    Funcionalidades principales:
    - Gestión de átomos de aprendizaje y sus relaciones
    - Tracking de progreso de usuarios
    - Generación de rutas de aprendizaje adaptativas
    - Análisis de dependencias y prerrequisitos
    - Recomendaciones personalizadas
    """

    def __init__(self, uri: str, user: str, password: str):
        self._driver = GraphDatabase.driver(uri, auth=(user, password))
        self._init_task = asyncio.create_task(self._initialize_schema())
        logger.info("Neo4jKnowledgeGraph initialized", uri=uri, user=user)

    async def _initialize_schema(self):
        """Inicializa el esquema del grafo con índices y restricciones"""
        try:
            with self._driver.session() as session:
                # Crear índices para átomos de aprendizaje (solo si no existen)
                try:
                    session.run("CREATE INDEX atom_title_index IF NOT EXISTS FOR (a:LearningAtom) ON (a.title)")
                    session.run("CREATE INDEX atom_difficulty_index IF NOT EXISTS FOR (a:LearningAtom) ON (a.difficulty_level)")
                    session.run("CREATE INDEX atom_tags_index IF NOT EXISTS FOR (a:LearningAtom) ON (a.tags)")
                except Exception as idx_error:
                    logger.warning("Some indexes already exist", error=str(idx_error))
                
                # Crear índices para usuarios
                try:
                    session.run("CREATE INDEX user_id_index IF NOT EXISTS FOR (u:User) ON (u.id)")
                except Exception as idx_error:
                    logger.warning("User index already exists", error=str(idx_error))
                
                # Crear restricciones de unicidad (manejar conflictos con índices existentes)
                try:
                    # Verificar si ya existe un índice en atom.id
                    result = session.run("SHOW INDEXES YIELD name, labelsOrTypes, properties WHERE 'LearningAtom' IN labelsOrTypes AND 'id' IN properties")
                    existing_indexes = list(result)
                    
                    if existing_indexes:
                        logger.info("Index on LearningAtom.id already exists, skipping constraint creation")
                    else:
                        session.run("CREATE CONSTRAINT atom_id_unique IF NOT EXISTS FOR (a:LearningAtom) REQUIRE a.id IS UNIQUE")
                except Exception as constraint_error:
                    logger.warning("Constraint creation failed", error=str(constraint_error))
                
                try:
                    # Similar para User.id
                    result = session.run("SHOW INDEXES YIELD name, labelsOrTypes, properties WHERE 'User' IN labelsOrTypes AND 'id' IN properties")
                    existing_user_indexes = list(result)
                    
                    if existing_user_indexes:
                        logger.info("Index on User.id already exists, skipping constraint creation")
                    else:
                        session.run("CREATE CONSTRAINT user_id_unique IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE")
                except Exception as constraint_error:
                    logger.warning("User constraint creation failed", error=str(constraint_error))
                
                logger.info("Neo4j schema initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize Neo4j schema", error=str(e))
            # No lanzar excepción para que los tests puedan continuar
            logger.warning("Continuing without full schema initialization")

    async def close(self):
        """Cierra la conexión a Neo4j"""
        if self._driver:
            self._driver.close()
            logger.info("Neo4j connection closed")

    # ========== GESTIÓN DE ÁTOMOS DE APRENDIZAJE ==========

    async def create_learning_atom(self, atom_data: Dict[str, Any]) -> str:
        """Crea un nuevo átomo de aprendizaje en el grafo"""
        await self._init_task
        
        atom_id = atom_data.get('id', str(uuid.uuid4()))
        
        query = """
        CREATE (a:LearningAtom {
            id: $id,
            title: $title,
            content: $content,
            difficulty_level: $difficulty_level,
            estimated_time_minutes: $estimated_time_minutes,
            tags: $tags,
            learning_objectives: $learning_objectives,
            created_at: datetime(),
            created_by_agent: $created_by_agent,
            agent_metadata: $agent_metadata
        })
        RETURN a.id as atom_id
        """
        
        with self._driver.session() as session:
            # Convertir agent_metadata a JSON string para Neo4j
            agent_metadata = atom_data.get('agent_metadata', {})
            agent_metadata_json = json.dumps(agent_metadata) if agent_metadata else "{}"
            
            result = session.run(query, 
                id=atom_id,
                title=atom_data.get('title', ''),
                content=atom_data.get('content', ''),
                difficulty_level=atom_data.get('difficulty_level', 'intermedio'),
                estimated_time_minutes=atom_data.get('estimated_time_minutes', 15),
                tags=atom_data.get('tags', []),
                learning_objectives=atom_data.get('learning_objectives', []),
                created_by_agent=atom_data.get('created_by_agent', True),
                agent_metadata=agent_metadata_json
            )
            
            record = result.single()
            created_id = record['atom_id'] if record else atom_id
            
            logger.info("Learning atom created", atom_id=created_id, title=atom_data.get('title'))
            return created_id

    async def create_prerequisite_relationship(self, atom_id: str, prerequisite_id: str, strength: float = 1.0):
        """Crea una relación de prerrequisito entre dos átomos"""
        await self._init_task
        
        query = """
        MATCH (atom:LearningAtom {id: $atom_id})
        MATCH (prereq:LearningAtom {id: $prerequisite_id})
        CREATE (atom)-[:REQUIRES {strength: $strength, created_at: datetime()}]->(prereq)
        RETURN atom.id, prereq.id
        """
        
        with self._driver.session() as session:
            result = session.run(query, 
                atom_id=atom_id,
                prerequisite_id=prerequisite_id,
                strength=strength
            )
            
            if result.single():
                logger.info("Prerequisite relationship created", 
                           atom=atom_id, prerequisite=prerequisite_id, strength=strength)
                return True
            return False

    async def get_learning_path_for_topic(self, topic: str, difficulty_level: Optional[str] = None, max_depth: int = 10) -> List[Dict[str, Any]]:
        """Obtiene una ruta de aprendizaje optimizada para un tema específico"""
        await self._init_task
        
        # Query simplificada que funciona correctamente
        query = """
        // Encontrar átomos relacionados con el tema
        MATCH (start:LearningAtom)
        WHERE $topic IN start.tags
        """ + (f"AND start.difficulty_level = '{difficulty_level}'" if difficulty_level else "") + """
        
        // Obtener la ruta completa de prerrequisitos
        CALL {
            WITH start
            MATCH path = (start)-[:REQUIRES*0..""" + str(max_depth) + """]->(prereq:LearningAtom)
            RETURN collect(DISTINCT prereq) as prerequisites
        }
        
        // Combinar átomo inicial con prerrequisitos
        WITH start, prerequisites
        UNWIND prerequisites + [start] as atom
        
        // Obtener información completa del átomo
        WITH DISTINCT atom
        RETURN atom {
            .id,
            .title,
            .content,
            .difficulty_level,
            .estimated_time_minutes,
            .tags,
            .learning_objectives
        } as atom_data
        ORDER BY 
            CASE atom_data.difficulty_level 
                WHEN 'básico' THEN 1
                WHEN 'intermedio' THEN 2
                WHEN 'avanzado' THEN 3
                ELSE 2
            END,
            atom_data.estimated_time_minutes
        """
        
        with self._driver.session() as session:
            result = session.run(query, topic=topic)
            atoms = [record['atom_data'] for record in result]
            
            logger.info("Learning path generated", 
                       topic=topic, difficulty=difficulty_level, atoms_count=len(atoms))
            return atoms

    # ========== GESTIÓN DE USUARIOS Y PROGRESO ==========

    async def create_or_update_user(self, user_id: str, user_data: Dict[str, Any]):
        """Crea o actualiza un usuario en el grafo"""
        await self._init_task
        
        query = """
        MERGE (u:User {id: $user_id})
        SET u.name = $name,
            u.learning_style = $learning_style,
            u.preferred_difficulty = $preferred_difficulty,
            u.updated_at = datetime()
        RETURN u.id
        """
        
        with self._driver.session() as session:
            result = session.run(query,
                user_id=user_id,
                name=user_data.get('name', ''),
                learning_style=user_data.get('learning_style', 'mixto'),
                preferred_difficulty=user_data.get('preferred_difficulty', 'intermedio')
            )
            
            if result.single():
                logger.info("User created/updated", user_id=user_id)
                return True
            return False

    async def update_user_progress(self, user_id: str, atom_id: str, mastery_level: float, evaluation_id: Optional[str] = None):
        """Actualiza el progreso de un usuario en un átomo específico"""
        await self._init_task
        
        query = """
        MATCH (u:User {id: $user_id})
        MATCH (a:LearningAtom {id: $atom_id})
        
        MERGE (u)-[p:PROGRESSED_IN]->(a)
        SET p.mastery_level = $mastery_level,
            p.last_updated = datetime(),
            p.evaluation_id = $evaluation_id,
            p.attempts = COALESCE(p.attempts, 0) + 1
        
        RETURN p.mastery_level, p.attempts
        """
        
        with self._driver.session() as session:
            result = session.run(query,
                user_id=user_id,
                atom_id=atom_id,
                mastery_level=mastery_level,
                evaluation_id=evaluation_id
            )
            
            record = result.single()
            if record:
                logger.info("User progress updated", 
                           user_id=user_id, atom_id=atom_id, mastery=mastery_level)
                return {
                    'mastery_level': record['p.mastery_level'],
                    'attempts': record['p.attempts']
                }
            return None

    async def get_user_progress_summary(self, user_id: str) -> Dict[str, Any]:
        """Obtiene un resumen completo del progreso del usuario"""
        await self._init_task
        
        query = """
        MATCH (u:User {id: $user_id})-[p:PROGRESSED_IN]->(a:LearningAtom)
        
        WITH u, 
             count(p) as total_atoms,
             avg(p.mastery_level) as avg_mastery,
             sum(CASE WHEN p.mastery_level >= 0.8 THEN 1 ELSE 0 END) as mastered_atoms,
             collect({
                 atom_id: a.id,
                 title: a.title,
                 mastery_level: p.mastery_level,
                 difficulty: a.difficulty_level,
                 last_updated: p.last_updated
             }) as progress_details
        
        RETURN {
            user_id: u.id,
            total_atoms: total_atoms,
            mastered_atoms: mastered_atoms,
            average_mastery: avg_mastery,
            mastery_percentage: (mastered_atoms * 100.0 / total_atoms),
            progress_details: progress_details
        } as summary
        """
        
        with self._driver.session() as session:
            result = session.run(query, user_id=user_id)
            record = result.single()
            
            if record:
                summary = record['summary']
                logger.info("User progress summary retrieved", 
                           user_id=user_id, total_atoms=summary['total_atoms'])
                return summary
            else:
                return {
                    'user_id': user_id,
                    'total_atoms': 0,
                    'mastered_atoms': 0,
                    'average_mastery': 0.0,
                    'mastery_percentage': 0.0,
                    'progress_details': []
                }

    # ========== RECOMENDACIONES ADAPTATIVAS ==========

    async def get_next_recommended_atoms(self, user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Obtiene los próximos átomos recomendados basados en el progreso del usuario"""
        await self._init_task
        
        # Query simplificada para recomendaciones
        query = """
        MATCH (u:User {id: $user_id})
        
        // Encontrar átomos que el usuario ha dominado
        OPTIONAL MATCH (u)-[mastered:PROGRESSED_IN]->(mastered_atom:LearningAtom)
        WHERE mastered.mastery_level >= 0.8
        
        // Encontrar átomos que requieren los dominados como prerrequisito
        OPTIONAL MATCH (next_atom:LearningAtom)-[:REQUIRES]->(mastered_atom)
        WHERE NOT EXISTS {
            MATCH (u)-[prog:PROGRESSED_IN]->(next_atom)
            WHERE prog.mastery_level >= 0.8
        }
        
        WITH DISTINCT next_atom
        WHERE next_atom IS NOT NULL
        
        RETURN next_atom {
            .id,
            .title,
            .difficulty_level,
            .estimated_time_minutes,
            .tags,
            .learning_objectives
        } as recommended_atom
        
        ORDER BY 
            CASE recommended_atom.difficulty_level 
                WHEN 'básico' THEN 1
                WHEN 'intermedio' THEN 2
                WHEN 'avanzado' THEN 3
                ELSE 2
            END,
            recommended_atom.estimated_time_minutes
        LIMIT $limit
        """
        
        with self._driver.session() as session:
            result = session.run(query, user_id=user_id, limit=limit)
            recommendations = [record['recommended_atom'] for record in result]
            
            logger.info("Recommendations generated", 
                       user_id=user_id, count=len(recommendations))
            return recommendations

    # ========== ANÁLISIS DEL GRAFO ==========

    async def get_knowledge_graph_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas generales del grafo de conocimiento"""
        await self._init_task
        
        query = """
        // Contar nodos y relaciones
        MATCH (atoms:LearningAtom)
        OPTIONAL MATCH (users:User)
        OPTIONAL MATCH ()-[prereqs:REQUIRES]->()
        OPTIONAL MATCH ()-[progress:PROGRESSED_IN]->()
        
        RETURN {
            total_atoms: count(DISTINCT atoms),
            total_users: count(DISTINCT users),
            total_prerequisites: count(DISTINCT prereqs),
            total_progress_records: count(DISTINCT progress)
        } as stats
        """
        
        with self._driver.session() as session:
            result = session.run(query)
            record = result.single()
            
            if record:
                stats = record['stats']
                logger.info("Knowledge graph stats retrieved", **stats)
                return stats
            return {}

    async def find_learning_gaps(self, user_id: str) -> List[Dict[str, Any]]:
        """Identifica brechas en el aprendizaje del usuario"""
        await self._init_task
        
        # Query simplificada para análisis de brechas
        query = """
        MATCH (u:User {id: $user_id})-[p:PROGRESSED_IN]->(atom:LearningAtom)
        WHERE p.mastery_level < 0.7  // Átomos no dominados
        
        // Encontrar prerrequisitos de estos átomos
        OPTIONAL MATCH (atom)-[:REQUIRES]->(prereq:LearningAtom)
        OPTIONAL MATCH (u)-[prereq_prog:PROGRESSED_IN]->(prereq)
        
        WITH atom, p, collect(CASE 
            WHEN prereq_prog IS NULL OR prereq_prog.mastery_level < 0.8 
            THEN prereq.title 
            ELSE NULL 
        END) as missing_prerequisites
        
        RETURN {
            atom_id: atom.id,
            atom_title: atom.title,
            current_mastery: p.mastery_level,
            difficulty: atom.difficulty_level,
            missing_prerequisites: missing_prerequisites
        } as gap
        
        ORDER BY gap.current_mastery ASC
        """
        
        with self._driver.session() as session:
            result = session.run(query, user_id=user_id)
            gaps = [record['gap'] for record in result]
            
            # Filtrar prerrequisitos nulos
            for gap in gaps:
                gap['missing_prerequisites'] = [p for p in gap['missing_prerequisites'] if p is not None]
            
            logger.info("Learning gaps identified", user_id=user_id, gaps_count=len(gaps))
            return gaps

    # ========== UTILIDADES ==========

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        asyncio.create_task(self.close())