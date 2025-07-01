"""
Test de integración para el sistema de grafo de conocimiento Neo4j.
Verifica la funcionalidad completa del repositorio agéntico.
"""

import pytest
import asyncio
import uuid
from typing import Dict, Any

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

from src.infrastructure.database.neo4j_knowledge_graph import Neo4jKnowledgeGraph

# Configuración de Neo4j para pruebas
NEO4J_CONFIG = {
    "uri": "bolt://localhost:7687",
    "user": "neo4j", 
    "password": "atomia123"
}

@pytest.fixture
def knowledge_graph():
    """Fixture que proporciona una instancia del grafo de conocimiento"""
    async def _get_kg():
        kg = Neo4jKnowledgeGraph(**NEO4J_CONFIG)
        await kg._init_task
        return kg
    
    return _get_kg

@pytest.mark.asyncio
class TestNeo4jKnowledgeGraph:
    """Tests de integración para el grafo de conocimiento agéntico"""

    async def test_create_learning_atoms_and_relationships(self, knowledge_graph):
        """Test 1: Crear átomos de aprendizaje y relaciones de prerrequisitos"""
        
        # Obtener instancia del grafo
        kg = await knowledge_graph()
        
        # Crear átomos de matemáticas básicas
        basic_atom = {
            'id': 'test_atom_basic_math',
            'title': 'Números Naturales',
            'content': 'Los números naturales son 1, 2, 3, 4...',
            'difficulty_level': 'básico',
            'estimated_time_minutes': 10,
            'tags': ['matemáticas', 'números', 'básico'],
            'learning_objectives': ['Identificar números naturales', 'Contar secuencialmente'],
            'created_by_agent': True,
            'agent_metadata': {
                'agent_type': 'atomization',
                'confidence': 0.95,
                'pedagogical_strategy': 'microlearning'
            }
        }
        
        intermediate_atom = {
            'id': 'test_atom_intermediate_math',
            'title': 'Suma y Resta',
            'content': 'Operaciones básicas de suma y resta con números naturales',
            'difficulty_level': 'intermedio',
            'estimated_time_minutes': 15,
            'tags': ['matemáticas', 'operaciones', 'suma', 'resta'],
            'learning_objectives': ['Realizar sumas', 'Realizar restas', 'Resolver problemas básicos'],
            'created_by_agent': True,
            'agent_metadata': {
                'agent_type': 'atomization',
                'confidence': 0.92,
                'pedagogical_strategy': 'active_learning'
            }
        }
        
        # Crear los átomos
        basic_id = await kg.create_learning_atom(basic_atom)
        intermediate_id = await kg.create_learning_atom(intermediate_atom)
        
        assert basic_id == 'test_atom_basic_math'
        assert intermediate_id == 'test_atom_intermediate_math'
        
        # Crear relación de prerrequisito: suma/resta requiere números naturales
        relationship_created = await kg.create_prerequisite_relationship(
            atom_id='test_atom_intermediate_math',
            prerequisite_id='test_atom_basic_math',
            strength=0.9
        )
        
        assert relationship_created is True
        
        # Limpiar datos de prueba
        with kg._driver.session() as session:
            session.run("MATCH (n:LearningAtom) WHERE n.id STARTS WITH 'test_atom_' DETACH DELETE n")
        
        await kg.close()
        
        print("✅ Test 1 completado: Átomos y relaciones creados exitosamente")

    async def test_generate_learning_path(self, knowledge_graph):
        """Test 2: Generar ruta de aprendizaje para un tema"""
        
        # Obtener instancia del grafo
        kg = await knowledge_graph()
        
        # Primero crear algunos átomos para la ruta
        atoms_data = [
            {
                'id': 'test_path_atom_1',
                'title': 'Conceptos Básicos de Álgebra',
                'difficulty_level': 'básico',
                'tags': ['álgebra', 'matemáticas'],
                'estimated_time_minutes': 20
            },
            {
                'id': 'test_path_atom_2',
                'title': 'Ecuaciones Lineales',
                'difficulty_level': 'intermedio',
                'tags': ['álgebra', 'ecuaciones'],
                'estimated_time_minutes': 25
            },
            {
                'id': 'test_path_atom_3',
                'title': 'Sistemas de Ecuaciones',
                'difficulty_level': 'avanzado',
                'tags': ['álgebra', 'sistemas'],
                'estimated_time_minutes': 30
            }
        ]
        
        # Crear los átomos
        for atom_data in atoms_data:
            await kg.create_learning_atom(atom_data)
        
        # Crear relaciones de prerrequisito
        await kg.create_prerequisite_relationship('test_path_atom_2', 'test_path_atom_1')
        await kg.create_prerequisite_relationship('test_path_atom_3', 'test_path_atom_2')
        
        # Generar ruta de aprendizaje para álgebra
        learning_path = await kg.get_learning_path_for_topic(
            topic='álgebra',
            difficulty_level=None,  # Todos los niveles
            max_depth=5
        )
        
        assert len(learning_path) == 3
        assert any(atom['id'] == 'test_path_atom_1' for atom in learning_path)
        assert any(atom['id'] == 'test_path_atom_2' for atom in learning_path)
        assert any(atom['id'] == 'test_path_atom_3' for atom in learning_path)
        
        # Verificar orden por dificultad (básico primero)
        difficulties = [atom['difficulty_level'] for atom in learning_path]
        assert difficulties[0] == 'básico'
        
        # Limpiar datos de prueba
        with kg._driver.session() as session:
            session.run("MATCH (n:LearningAtom) WHERE n.id STARTS WITH 'test_path_atom_' DETACH DELETE n")
        
        await kg.close()
        
        print("✅ Test 2 completado: Ruta de aprendizaje generada correctamente")

    async def test_user_progress_tracking(self, knowledge_graph):
        """Test 3: Seguimiento de progreso de usuario"""
        
        # Obtener instancia del grafo
        kg = await knowledge_graph()
        
        user_id = f"test_user_progress_{uuid.uuid4().hex[:8]}"
        
        # Crear usuario
        user_created = await kg.create_or_update_user(
            user_id=user_id,
            user_data={
                'name': 'Usuario de Prueba',
                'learning_style': 'visual',
                'preferred_difficulty': 'intermedio'
            }
        )
        assert user_created is True
        
        # Crear algunos átomos para el progreso
        atom_ids = []
        for i in range(3):
            atom_data = {
                'id': f'test_progress_atom_{i}',
                'title': f'Átomo de Progreso {i+1}',
                'difficulty_level': 'intermedio',
                'tags': ['progreso', 'test'],
                'estimated_time_minutes': 15
            }
            atom_id = await kg.create_learning_atom(atom_data)
            atom_ids.append(atom_id)
        
        # Actualizar progreso del usuario
        progress_updates = [
            {'atom_id': atom_ids[0], 'mastery_level': 0.9, 'evaluation_id': 'eval_1'},
            {'atom_id': atom_ids[1], 'mastery_level': 0.7, 'evaluation_id': 'eval_2'},
            {'atom_id': atom_ids[2], 'mastery_level': 0.6, 'evaluation_id': 'eval_3'}
        ]
        
        for update in progress_updates:
            result = await kg.update_user_progress(
                user_id=user_id,
                atom_id=update['atom_id'],
                mastery_level=update['mastery_level'],
                evaluation_id=update['evaluation_id']
            )
            assert result is not None
            assert result['mastery_level'] == update['mastery_level']
            assert result['attempts'] >= 1
        
        # Obtener resumen de progreso
        progress_summary = await kg.get_user_progress_summary(user_id)
        
        assert progress_summary['user_id'] == user_id
        assert progress_summary['total_atoms'] == 3
        assert progress_summary['mastered_atoms'] == 1  # Solo uno con mastery >= 0.8
        assert 0.7 <= progress_summary['average_mastery'] <= 0.8
        assert len(progress_summary['progress_details']) == 3
        
        # Limpiar datos de prueba
        with kg._driver.session() as session:
            session.run(f"MATCH (n:LearningAtom) WHERE n.id STARTS WITH 'test_progress_atom_' DETACH DELETE n")
            session.run(f"MATCH (n:User) WHERE n.id = '{user_id}' DETACH DELETE n")
        
        await kg.close()
        
        print("✅ Test 3 completado: Progreso de usuario rastreado correctamente")

    async def test_adaptive_recommendations(self, knowledge_graph):
        """Test 4: Recomendaciones adaptativas basadas en progreso"""
        
        user_id = f"test_user_recommendations_{uuid.uuid4().hex[:8]}"
        
        # Crear usuario
        await knowledge_graph.create_or_update_user(
            user_id=user_id,
            user_data={'name': 'Usuario Recomendaciones', 'learning_style': 'kinestésico'}
        )
        
        # Crear una secuencia de átomos con prerrequisitos
        atoms_sequence = [
            {'id': 'test_rec_atom_1', 'title': 'Fundamentos', 'difficulty_level': 'básico'},
            {'id': 'test_rec_atom_2', 'title': 'Intermedio A', 'difficulty_level': 'intermedio'},
            {'id': 'test_rec_atom_3', 'title': 'Intermedio B', 'difficulty_level': 'intermedio'},
            {'id': 'test_rec_atom_4', 'title': 'Avanzado', 'difficulty_level': 'avanzado'}
        ]
        
        # Crear los átomos
        for atom in atoms_sequence:
            atom['tags'] = ['recomendaciones', 'test']
            atom['estimated_time_minutes'] = 20
            await knowledge_graph.create_learning_atom(atom)
        
        # Crear cadena de prerrequisitos: 4 -> 3 -> 2 -> 1, 4 -> 2 -> 1
        await knowledge_graph.create_prerequisite_relationship('test_rec_atom_2', 'test_rec_atom_1')
        await knowledge_graph.create_prerequisite_relationship('test_rec_atom_3', 'test_rec_atom_2')
        await knowledge_graph.create_prerequisite_relationship('test_rec_atom_4', 'test_rec_atom_2')
        await knowledge_graph.create_prerequisite_relationship('test_rec_atom_4', 'test_rec_atom_3')
        
        # Usuario domina el primer átomo
        await knowledge_graph.update_user_progress(user_id, 'test_rec_atom_1', 0.9)
        
        # Obtener recomendaciones
        recommendations = await knowledge_graph.get_next_recommended_atoms(user_id, limit=5)
        
        # Debería recomendar el átomo 2 (intermedio A) ya que el usuario dominó el 1
        assert len(recommendations) >= 1
        recommended_ids = [rec['id'] for rec in recommendations]
        assert 'test_rec_atom_2' in recommended_ids
        
        # No debería recomendar átomos avanzados sin prerrequisitos completados
        assert 'test_rec_atom_4' not in recommended_ids
        
        print("✅ Test 4 completado: Recomendaciones adaptativas funcionando")

    async def test_learning_gaps_analysis(self, knowledge_graph):
        """Test 5: Análisis de brechas de aprendizaje"""
        
        user_id = f"test_user_gaps_{uuid.uuid4().hex[:8]}"
        
        # Crear usuario
        await knowledge_graph.create_or_update_user(
            user_id=user_id,
            user_data={'name': 'Usuario Brechas'}
        )
        
        # Crear átomos con prerrequisitos
        gap_atoms = [
            {'id': 'test_gap_prereq', 'title': 'Prerrequisito', 'difficulty_level': 'básico'},
            {'id': 'test_gap_main', 'title': 'Átomo Principal', 'difficulty_level': 'intermedio'}
        ]
        
        for atom in gap_atoms:
            atom['tags'] = ['gaps', 'test']
            atom['estimated_time_minutes'] = 15
            await knowledge_graph.create_learning_atom(atom)
        
        # Crear relación de prerrequisito
        await knowledge_graph.create_prerequisite_relationship('test_gap_main', 'test_gap_prereq')
        
        # Usuario tiene progreso bajo en el átomo principal pero no domina el prerrequisito
        await knowledge_graph.update_user_progress(user_id, 'test_gap_main', 0.5)  # Bajo dominio
        await knowledge_graph.update_user_progress(user_id, 'test_gap_prereq', 0.6)  # Prerrequisito no dominado
        
        # Analizar brechas de aprendizaje
        learning_gaps = await knowledge_graph.find_learning_gaps(user_id)
        
        assert len(learning_gaps) >= 1
        
        # Verificar que identifica la brecha
        main_gap = next((gap for gap in learning_gaps if gap['atom_id'] == 'test_gap_main'), None)
        assert main_gap is not None
        assert main_gap['current_mastery'] == 0.5
        assert 'Prerrequisito' in main_gap['missing_prerequisites']
        
        print("✅ Test 5 completado: Análisis de brechas funcionando")

    async def test_knowledge_graph_statistics(self, knowledge_graph):
        """Test 6: Estadísticas del grafo de conocimiento"""
        
        # Las estadísticas incluirán todos los datos creados en tests anteriores
        stats = await knowledge_graph.get_knowledge_graph_stats()
        
        assert 'total_atoms' in stats
        assert 'total_users' in stats
        assert 'total_prerequisites' in stats
        assert 'total_progress_records' in stats
        
        # Verificar que hay datos
        assert stats['total_atoms'] > 0
        assert stats['total_users'] > 0
        
        print(f"✅ Test 6 completado: Estadísticas del grafo - {stats}")

if __name__ == "__main__":
    # Ejecutar tests individualmente para debugging
    async def run_single_test():
        kg = Neo4jKnowledgeGraph(**NEO4J_CONFIG)
        await kg._init_task
        
        # Ejecutar un test específico
        test_instance = TestNeo4jKnowledgeGraph()
        await test_instance.test_create_learning_atoms_and_relationships(kg)
        
        await kg.close()
    
    # asyncio.run(run_single_test())
    print("Tests de Neo4j listos para ejecutar con pytest") 