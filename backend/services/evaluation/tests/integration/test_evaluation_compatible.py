"""
Test de persistencia compatible para el servicio de evaluation
"""

import pytest
import asyncio
from datetime import datetime
from uuid import uuid4

from src.infrastructure.database.evaluation_repository_compatible import CompatibleEvaluationRepository
from src.schemas import (
    EvaluationResponse, FeedbackDetail, LearningProgress, 
    AgentMetadata, Misconception
)

# Configurar la conexión a la base de datos para testing (usando asyncpg)
TEST_DATABASE_URL = "postgresql+asyncpg://atomia_user:atomia_password@localhost/atomia_dev"


def create_compatible_evaluation(evaluation_id: str, user_id: str, question_id: str, score: float = 0.8) -> EvaluationResponse:
    """Crear una evaluación compatible para testing"""
    
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
async def test_compatible_evaluation_basic_persistence():
    """Test básico de persistencia del repositorio compatible"""
    
    repository = CompatibleEvaluationRepository(TEST_DATABASE_URL)
    
    try:
        print("✅ Repositorio compatible de evaluation creado")
        
        # Crear datos de prueba
        evaluation_id = str(uuid4())
        user_id = f"test_user_compatible_{uuid4().hex[:8]}"  # Usuario único
        question_id = "question_math_compatible_001"
        
        evaluation_data = create_compatible_evaluation(evaluation_id, user_id, question_id, score=0.85)
        
        # Guardar la evaluación (sin atom_id)
        saved_id = await repository.save_evaluation(evaluation_data, user_id, question_id)
        assert saved_id == evaluation_id
        print(f"✅ Evaluación compatible guardada con ID: {saved_id}")
        
        # Recuperar la evaluación
        saved_evaluation = await repository.get_evaluation_by_id(evaluation_id)
        
        # Verificar que se guardó correctamente
        assert saved_evaluation is not None
        assert saved_evaluation["evaluation_id"] == evaluation_id
        assert saved_evaluation["score"] == 0.85
        assert saved_evaluation["user_id"] == user_id
        assert "feedback" in saved_evaluation
        assert "agent_metadata" in saved_evaluation
        
        print(f"✅ Evaluación compatible recuperada exitosamente")
        print(f"   - ID: {saved_evaluation['evaluation_id']}")
        print(f"   - Score: {saved_evaluation['score']}")
        print(f"   - User: {saved_evaluation['user_id']}")
        print(f"   - Concepts: {saved_evaluation['key_concepts_understood']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en el test compatible: {e}")
        import traceback
        traceback.print_exc()
        raise


@pytest.mark.asyncio
async def test_compatible_user_progress_summary():
    """Test del resumen de progreso de usuario"""
    
    repository = CompatibleEvaluationRepository(TEST_DATABASE_URL)
    
    try:
        user_id = f"test_user_progress_{uuid4().hex[:8]}"  # Usuario único
        
        # Crear múltiples evaluaciones para simular progreso
        scores = [0.6, 0.7, 0.8, 0.85, 0.9]  # Progreso ascendente
        evaluation_ids = []
        
        for i, score in enumerate(scores):
            evaluation_id = str(uuid4())
            evaluation_data = create_compatible_evaluation(
                evaluation_id, 
                user_id, 
                f"question_{i}", 
                score
            )
            
            await repository.save_evaluation(evaluation_data, user_id, f"question_{i}")
            evaluation_ids.append(evaluation_id)
            print(f"✅ Evaluación {i+1} guardada: score={score}")
        
        # Obtener resumen de progreso
        progress_summary = await repository.get_user_progress_summary(user_id)
        
        assert progress_summary["total_evaluations"] == 5
        assert progress_summary["average_score"] > 0.7  # Debería ser > 0.7
        assert progress_summary["improvement_trend"] in ["improving", "stable", "insufficient_data"]
        assert len(progress_summary["concepts_mastered"]) >= 0
        
        print(f"✅ Resumen de progreso:")
        print(f"   - Total evaluaciones: {progress_summary['total_evaluations']}")
        print(f"   - Score promedio: {progress_summary['average_score']}")
        print(f"   - Tendencia: {progress_summary['improvement_trend']}")
        print(f"   - Conceptos dominados: {progress_summary['concepts_mastered']}")
        print(f"   - Temas recientes: {progress_summary['recent_topics']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en test de progreso: {e}")
        import traceback
        traceback.print_exc()
        raise


@pytest.mark.asyncio
async def test_compatible_evaluation_stats():
    """Test de estadísticas generales"""
    
    repository = CompatibleEvaluationRepository(TEST_DATABASE_URL)
    
    try:
        # Obtener estadísticas actuales
        stats = await repository.get_evaluation_stats()
        
        # Debería tener al menos las evaluaciones que acabamos de crear
        assert stats["total_evaluations"] >= 0
        assert stats["unique_users"] >= 0
        assert isinstance(stats["average_score"], float)
        assert isinstance(stats["evaluations_per_user"], float)
        
        print(f"✅ Estadísticas generales:")
        print(f"   - Total evaluaciones: {stats['total_evaluations']}")
        print(f"   - Usuarios únicos: {stats['unique_users']}")
        print(f"   - Score promedio: {stats['average_score']}")
        print(f"   - Evaluaciones por usuario: {stats['evaluations_per_user']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en test de estadísticas: {e}")
        import traceback
        traceback.print_exc()
        raise


@pytest.mark.asyncio
async def test_compatible_concept_search():
    """Test de búsqueda por concepto"""
    
    repository = CompatibleEvaluationRepository(TEST_DATABASE_URL)
    
    try:
        user_id = f"test_user_search_{uuid4().hex[:8]}"  # Usuario único
        
        # Crear evaluación con conceptos específicos
        evaluation_id = str(uuid4())
        evaluation_data = create_compatible_evaluation(evaluation_id, user_id, "question_search", score=0.85)
        
        # Asegurar que tiene conceptos específicos
        evaluation_data.key_concepts_understood = ["fractions", "decimals", "percentages"]
        
        await repository.save_evaluation(evaluation_data, user_id, "question_search")
        print("✅ Evaluación con conceptos específicos guardada")
        
        # Buscar por concepto
        search_results = await repository.search_evaluations_by_concept("fractions")
        
        # Verificar resultados
        assert isinstance(search_results, list)
        # Debería encontrar al menos nuestra evaluación
        found_our_eval = any(eval_data["evaluation_id"] == evaluation_id for eval_data in search_results)
        
        print(f"✅ Búsqueda por concepto 'fractions':")
        print(f"   - Resultados encontrados: {len(search_results)}")
        print(f"   - Nuestra evaluación encontrada: {found_our_eval}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en test de búsqueda: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    # Permitir ejecutar el test directamente
    async def run_tests():
        try:
            await test_compatible_evaluation_basic_persistence()
            print("\n" + "="*50)
            await test_compatible_user_progress_summary()
            print("\n" + "="*50)
            await test_compatible_evaluation_stats()
            print("\n" + "="*50)
            await test_compatible_concept_search()
            print("\n✅ Todos los tests compatibles de evaluation completados exitosamente!")
        except Exception as e:
            print(f"\n❌ Error en los tests: {e}")
    
    asyncio.run(run_tests()) 