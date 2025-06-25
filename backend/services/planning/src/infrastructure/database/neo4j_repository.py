from typing import List, Dict, Any, Optional
from neo4j import GraphDatabase
import structlog

logger = structlog.get_logger(__name__)

class Neo4jPlanningRepository:
    """
    Repositorio para leer el grafo de conocimiento de Neo4j y
    extraer rutas de aprendizaje.
    """

    def __init__(self, uri: str, user: str, password: str):
        self._driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self._driver.close()

    async def get_learning_path_for_topic(self, topic: str) -> List[Dict[str, Any]]:
        """
        Obtiene una ruta de aprendizaje (secuencia de átomos) para un tema.

        Encuentra todos los átomos etiquetados con el tema y sus dependencias,
        y los devuelve en un orden topológico.
        """
        query = """
        // 1. Encontrar todos los átomos relacionados con el tema
        MATCH (start_atom:LearningAtom)
        WHERE $topic IN start_atom.tags

        // 2. Encontrar todos los prerrequisitos de forma recursiva
        CALL {
            WITH start_atom
            MATCH path = (dependent:LearningAtom)-[:REQUIRES*0..]->(prereq:LearningAtom)
            WHERE dependent = start_atom
            RETURN collect(nodes(path)) as all_nodes_nested
        }

        // 3. Desanidar y obtener nodos únicos
        UNWIND all_nodes_nested as node_list
        UNWIND node_list as atom_node
        WITH collect(DISTINCT atom_node) as atoms

        // 4. Devolver los átomos (se ordenarán en la lógica de negocio)
        RETURN atoms
        """
        with self._driver.session() as session:
            result = session.run(query, topic=topic)
            # Extraer los datos de los nodos
            raw_atoms = result.single()
            if raw_atoms and 'atoms' in raw_atoms:
                return [dict(record) for record in raw_atoms['atoms']]
            return []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close() 