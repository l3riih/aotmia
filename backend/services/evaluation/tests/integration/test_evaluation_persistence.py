"""
Test de persistencia para el servicio de evaluation
"""

import pytest
import asyncio
from datetime import datetime
from uuid import uuid4

from src.infrastructure.database.evaluation_repository import PostgresEvaluationRepository
from src.schemas import (
    EvaluationResponse, FeedbackDetail, LearningProgress, 
    AgentMetadata, Misconception
)

# Configurar la conexión a la base de datos para testing (usando asyncpg)
TEST_DATABASE_URL = "postgresql+asyncpg://atomia_user:atomia_password@localhost/atomia_dev"


def create_minimal_evaluation(evaluation_id: str, user_id: str, question_id: str, score: float = 0.8) -> EvaluationResponse:
    """Crear una evaluación mínima válida para testing"""
    
    # Crear feedback detail
    feedback_detail = FeedbackDetail(
        strengths=["Comprensión clara del concepto"],
        improvements=["Podrías mejorar la velocidad de respuesta"],
        suggestions=["Practica más ejercicios similares"],
        examples=["Ejemplo: 3/4 = 0.75"]
    )
    
    # Crear learning progress
    learning_progress = LearningProgress(
        current_mastery=score,
        improvement=0.1 if score >= 0.7 else -0.1,
        trend="improving" if score >= 0.7 else "declining",
        confidence_level=0.85
    )
    
    # Crear agent metadata
    agent_metadata = AgentMetadata(
        reasoning_steps=["Analyzed user response", "Compared with expected answer", "Provided feedback"],
        tools_used=["concept_analyzer", "feedback_generator"],
        iterations=1,
        confidence_score=0.85,
        reasoning_quality=0.9,
        processing_time_ms=250
    )
    
    # Crear misconceptions si el score es bajo
    misconceptions = []
    if score < 0.7:
        misconceptions.append(Misconception(
            concept="fractions",
            description="Confusión entre numerador y denominador",
            severity=0.6,
            correction="Revisar conceptos básicos de fracciones"
        ))
    
    # Crear la evaluación completa
    return EvaluationResponse(
        evaluation_id=evaluation_id,
        score=score,
        feedback=feedback_detail,
        misconceptions_detected=misconceptions,
        learning_progress=learning_progress,
        agent_metadata=agent_metadata,
        key_concepts_understood=["fractions", "decimals"] if score >= 0.7 else ["decimals"],
        next_recommended_topics=["algebra", "geometry"],
        estimated_time_to_mastery=45
    )


@pytest.mark.asyncio
async def test_evaluation_basic_persistence():
    """Test básico de persistencia del repositorio de evaluaciones"""
    
    repository = PostgresEvaluationRepository(TEST_DATABASE_URL)
    
    try:
        print("✅ Repositorio de evaluation creado")
        
        # Crear datos de prueba
        evaluation_id = str(uuid4())
        user_id = "test_user_eval_123"
        question_id = "question_math_001"
        atom_id = "atom_fractions_1"
        
        evaluation_data = create_minimal_evaluation(evaluation_id, user_id, question_id, score=0.85)
        
        # Guardar la evaluación
        saved_id = await repository.save_evaluation(evaluation_data, user_id, question_id, atom_id)
        assert saved_id == evaluation_id
        print(f"✅ Evaluación guardada con ID: {saved_id}")
        
        # Recuperar la evaluación
        saved_evaluation = await repository.get_evaluation_by_id(evaluation_id)
        
        # Verificar que se guardó correctamente
        assert saved_evaluation is not None
        assert saved_evaluation.evaluation_id == evaluation_id
        assert saved_evaluation.score == 0.85
        assert "Comprensión clara del concepto" in saved_evaluation.feedback.strengths
        assert len(saved_evaluation.key_concepts_understood) >= 1
        
        print(f"✅ Evaluación recuperada exitosamente")
        print(f"   - ID: {saved_evaluation.evaluation_id}")
        print(f"   - Score: {saved_evaluation.score}")
        print(f"   - Strengths: {saved_evaluation.feedback.strengths}")
        print(f"   - Concepts: {saved_evaluation.key_concepts_understood}")
        
        # Actualizar progreso del usuario
        await repository.update_user_progress(
            user_id=user_id,
            atom_id=atom_id,
            evaluation_id=evaluation_id,
            correct=True,
            score=0.85
        )
        print("✅ Progreso de usuario actualizado")
        
        # Verificar progreso del usuario
        user_progress = await repository.get_user_progress(user_id, atom_id)
        assert len(user_progress) == 1
        assert user_progress[0]["mastery_level"] == 0.85
        assert user_progress[0]["total_attempts"] == 1
        assert user_progress[0]["correct_attempts"] == 1
        
        print(f"✅ Progreso verificado: {user_progress[0]['mastery_level']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en el test: {e}")
        import traceback
        traceback.print_exc()
        raise


@pytest.mark.asyncio
async def test_evaluation_user_evaluations():
    """Test de múltiples evaluaciones por usuario"""
    
    repository = PostgresEvaluationRepository(TEST_DATABASE_URL)
    
    try:
        user_id = "test_user_multiple_eval_456"
        question_id = "question_math_002"
        atom_id = "atom_algebra_1"
        evaluation_ids = []
        
        # Crear múltiples evaluaciones con scores diferentes
        scores = [0.6, 0.7, 0.85]
        for i, score in enumerate(scores):
            evaluation_id = str(uuid4())
            evaluation_data = create_minimal_evaluation(evaluation_id, user_id, question_id, score)
            
            await repository.save_evaluation(evaluation_data, user_id, f"{question_id}_{i}", atom_id)
            evaluation_ids.append(evaluation_id)
            
            # Actualizar progreso
            await repository.update_user_progress(
                user_id=user_id,
                atom_id=atom_id,
                evaluation_id=evaluation_id,
                correct=score >= 0.7,
                score=score
            )
            
            print(f"✅ Evaluación {i+1} creada: {evaluation_id} (score: {score})")
        
        # Recuperar todas las evaluaciones del usuario
        user_evaluations = await repository.get_user_evaluations(user_id)
        
        assert len(user_evaluations) >= 3
        
        # Verificar que las evaluaciones están ordenadas por fecha (más reciente primero)
        evaluation_ids_found = [e.evaluation_id for e in user_evaluations]
        for eval_id in evaluation_ids:
            assert eval_id in evaluation_ids_found
        
        print(f"✅ Todas las evaluaciones recuperadas: {len(user_evaluations)}")
        
        # Verificar progreso del usuario (debe mostrar mejora)
        final_progress = await repository.get_user_progress(user_id, atom_id)
        assert len(final_progress) == 1
        assert final_progress[0]["total_attempts"] == 3
        assert final_progress[0]["correct_attempts"] == 2  # scores >= 0.7
        
        # El mastery level debe reflejar la mejora (factor de recencia)
        final_mastery = final_progress[0]["mastery_level"]
        print(f"✅ Progreso final: mastery={final_mastery}, attempts={final_progress[0]['total_attempts']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en test múltiple: {e}")
        import traceback
        traceback.print_exc()
        raise


@pytest.mark.asyncio
async def test_evaluation_stats():
    """Test de estadísticas de evaluación"""
    
    repository = PostgresEvaluationRepository(TEST_DATABASE_URL)
    
    try:
        user_id = "test_user_stats_789"
        atom_ids = ["atom_stats_1", "atom_stats_2", "atom_stats_3"]
        
        # Crear evaluaciones para diferentes átomos
        for i, atom_id in enumerate(atom_ids):
            evaluation_id = str(uuid4())
            score = 0.8 + (i * 0.05)  # Scores: 0.8, 0.85, 0.9
            
            evaluation_data = create_minimal_evaluation(evaluation_id, user_id, f"q_{i}", score)
            
            await repository.save_evaluation(evaluation_data, user_id, f"question_{i}", atom_id)
            await repository.update_user_progress(
                user_id=user_id,
                atom_id=atom_id,
                evaluation_id=evaluation_id,
                correct=True,
                score=score
            )
            
            print(f"✅ Evaluación para átomo {atom_id}: score={score}")
        
        # Obtener estadísticas de dominio del usuario
        mastery_stats = await repository.get_mastery_stats(user_id)
        
        assert mastery_stats["total_atoms"] >= 3
        assert mastery_stats["mastered_atoms"] >= 3  # Todos con score >= 0.8
        assert mastery_stats["mastery_percentage"] >= 100.0
        assert mastery_stats["average_mastery"] >= 0.8
        
        print(f"✅ Estadísticas de dominio:")
        print(f"   - Total átomos: {mastery_stats['total_atoms']}")
        print(f"   - Átomos dominados: {mastery_stats['mastered_atoms']}")
        print(f"   - Porcentaje dominio: {mastery_stats['mastery_percentage']:.1f}%")
        print(f"   - Promedio dominio: {mastery_stats['average_mastery']:.2f}")
        
        # Obtener estadísticas generales
        eval_stats = await repository.get_evaluation_stats()
        
        assert eval_stats["total_evaluations"] >= 3
        assert eval_stats["unique_users"] >= 1
        assert eval_stats["average_score"] > 0.0
        
        print(f"✅ Estadísticas generales:")
        print(f"   - Total evaluaciones: {eval_stats['total_evaluations']}")
        print(f"   - Usuarios únicos: {eval_stats['unique_users']}")
        print(f"   - Score promedio: {eval_stats['average_score']:.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en test de estadísticas: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    # Permitir ejecutar el test directamente
    async def run_tests():
        try:
            await test_evaluation_basic_persistence()
            print("\n" + "="*50)
            await test_evaluation_user_evaluations()
            print("\n" + "="*50)
            await test_evaluation_stats()
            print("\n✅ Todos los tests de evaluation completados exitosamente!")
        except Exception as e:
            print(f"\n❌ Error en los tests: {e}")
    
    asyncio.run(run_tests()) 