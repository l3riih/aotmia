from typing import List, Dict, Any
from neo4j import GraphDatabase
import structlog

logger = structlog.get_logger(__name__)

class Neo4jRepository:
    """
    Repositorio para interactuar con la base de datos de grafos Neo4j.
    Gestiona los nodos de átomos de aprendizaje y sus relaciones.
    """

    def __init__(self, uri, user, password):
        self._driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self._driver.close()

    async def save_atoms_with_relationships(self, atoms: List[Dict[str, Any]]):
        """
        Guarda una lista de átomos y establece sus relaciones de prerrequisitos
        de forma transaccional.
        """
        if not atoms:
            logger.info("No atoms to save in Neo4j.")
            return

        with self._driver.session() as session:
            # Usar execute_write para asegurar la atomicidad de la operación
            session.execute_write(self._create_atom_nodes_tx, atoms)
            session.execute_write(self._create_relationships_tx, atoms)
        
        logger.info(
            "Finished saving atoms and relationships to Neo4j.",
            atoms_processed=len(atoms)
        )

    @staticmethod
    def _create_atom_nodes_tx(tx, atoms: List[Dict[str, Any]]):
        """Crea o actualiza los nodos de los átomos de aprendizaje."""
        query = """
        UNWIND $atoms as atom_data
        MERGE (a:LearningAtom {id: atom_data.id})
        SET a.title = atom_data.title,
            a.difficulty_level = atom_data.difficulty_level,
            a.tags = atom_data.tags,
            a.created_at = datetime()
        """
        
        # Preparar los datos para la consulta
        atoms_to_save = []
        for atom in atoms:
            # Asegurarse de que el ID es un string para Neo4j
            atom_id = str(atom.get('id'))
            if not atom_id:
                continue

            atoms_to_save.append({
                "id": atom_id,
                "title": atom.get('title', 'Sin Título'),
                "difficulty_level": atom.get('difficulty_level', 'intermedio'),
                "tags": atom.get('tags', [])
            })
        
        if atoms_to_save:
            tx.run(query, atoms=atoms_to_save)

    @staticmethod
    def _create_relationships_tx(tx, atoms: List[Dict[str, Any]]):
        """Crea las relaciones de prerrequisitos entre los átomos."""
        query = """
        UNWIND $relations as relation
        MATCH (a:LearningAtom {id: relation.atom_id})
        MATCH (p:LearningAtom {id: relation.prereq_id})
        MERGE (a)-[:REQUIRES]->(p)
        """
        
        relations_to_create = []
        for atom in atoms:
            atom_id = str(atom.get('id'))
            if not atom_id or not atom.get('prerequisites'):
                continue
            
            for prereq_id in atom.get('prerequisites'):
                relations_to_create.append({
                    "atom_id": atom_id,
                    "prereq_id": str(prereq_id)
                })

        if relations_to_create:
            tx.run(query, relations=relations_to_create)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close() 