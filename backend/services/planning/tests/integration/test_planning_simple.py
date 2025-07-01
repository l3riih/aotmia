"""
Test simple de persistencia - Prueba directa del repositorio
"""

import pytest
import asyncio
from datetime import datetime
from uuid import uuid4

from src.infrastructure.database.planning_repository import PostgresPlanningRepository
from src.schemas import (
    LearningPlanResponse, PlanStatus, LearningPath, Schedule, 
    AgentPlanningMetadata, LearningPhase, DailySession, DifficultyLevel
)

# Configurar la conexión a la base de datos para testing (usando asyncpg)
TEST_DATABASE_URL = "postgresql+asyncpg://atomia_user:atomia_password@localhost/atomia_dev"


def create_minimal_plan(plan_id: str, user_id: str) -> LearningPlanResponse:
    """Crear un plan mínimo válido para testing"""
    
    # Crear una fase simple
    phase = LearningPhase(
        phase_id=1,
        name="Fase 1",
        atoms=["atom_1"],
        estimated_duration_minutes=30,
        objectives=["Objetivo 1"],
        prerequisites_completed=True,
        difficulty_level=DifficultyLevel.BASICO
    )
    
    # Crear un learning path simple
    learning_path = LearningPath(
        total_atoms=1,
        estimated_time_hours=0.5,
        difficulty_progression="gradual",
        phases=[phase],
        dependency_graph={"atom_1": []}
    )
    
    # Crear una sesión diaria simple
    daily_session = DailySession(
        day=1,
        atoms=["atom_1"],
        review_atoms=[],
        estimated_time_minutes=30,
        session_type="new_content"
    )
    
    # Crear un schedule simple
    schedule = Schedule(
        daily_sessions=[daily_session],
        total_days=1,
        review_frequency="daily",
        estimated_completion_date=None
    )
    
    # Crear metadata del agente
    agent_metadata = AgentPlanningMetadata(
        reasoning_steps=["Plan created for testing"],
        tools_used=["test_tool"],
        confidence_score=0.8,
        algorithms_applied=["basic"],
        iterations=1,
        processing_time_ms=100,
        adaptability_score=0.7
    )
    
    # Crear el plan completo
    return LearningPlanResponse(
        plan_id=plan_id,
        user_id=user_id,
        status=PlanStatus.ACTIVE,
        learning_path=learning_path,
        schedule=schedule,
        agent_metadata=agent_metadata,
        created_at=datetime.now(),
        updated_at=None,
        predicted_success_rate=0.8,
        estimated_mastery_level=0.7,
        risk_factors=[]
    )


@pytest.mark.asyncio
async def test_repository_basic_persistence():
    """Test básico de persistencia del repositorio"""
    
    repository = PostgresPlanningRepository(TEST_DATABASE_URL)
    
    try:
        print("✅ Repositorio creado")
        
        # Crear un plan de prueba
        plan_id = str(uuid4())
        user_id = "test_user_simple_123"
        
        plan_data = create_minimal_plan(plan_id, user_id)
        
        # Guardar el plan
        await repository.save(plan_data)
        print(f"✅ Plan guardado con ID: {plan_data.plan_id}")
        
        # Recuperar el plan
        saved_plan = await repository.get(plan_data.plan_id)
        
        # Verificar que se guardó correctamente
        assert saved_plan is not None
        assert saved_plan.plan_id == plan_data.plan_id
        assert saved_plan.user_id == plan_data.user_id
        assert saved_plan.status == plan_data.status
        
        print(f"✅ Plan recuperado exitosamente")
        print(f"   - ID: {saved_plan.plan_id}")
        print(f"   - User: {saved_plan.user_id}")
        print(f"   - Status: {saved_plan.status}")
        print(f"   - Total atoms: {saved_plan.learning_path.total_atoms}")
        
        # Actualizar el plan
        saved_plan.status = PlanStatus.COMPLETED
        saved_plan.updated_at = datetime.now()
        
        await repository.update(saved_plan)
        print("✅ Plan actualizado")
        
        # Verificar la actualización
        updated_plan = await repository.get(plan_data.plan_id)
        assert updated_plan.status == PlanStatus.COMPLETED
        print(f"✅ Actualización verificada: status = {updated_plan.status}")
        
        # Probar obtener planes por usuario
        user_plans = await repository.get_user_plans(plan_data.user_id)
        assert len(user_plans) >= 1
        
        # Verificar que nuestro plan está en la lista
        plan_ids = [p.plan_id for p in user_plans]
        assert plan_data.plan_id in plan_ids
        
        print(f"✅ Planes de usuario recuperados: {len(user_plans)} plan(es)")
        
        # Probar estadísticas del repositorio
        stats = await repository.get_stats()
        print(f"✅ Estadísticas obtenidas: {stats}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en el test: {e}")
        import traceback
        traceback.print_exc()
        raise


@pytest.mark.asyncio
async def test_repository_multiple_plans():
    """Test de múltiples planes para verificar la funcionalidad completa"""
    
    repository = PostgresPlanningRepository(TEST_DATABASE_URL)
    
    try:
        user_id = "test_user_multiple_456"
        plan_ids = []
        
        # Crear múltiples planes
        for i in range(3):
            plan_id = str(uuid4())
            plan_data = create_minimal_plan(plan_id, user_id)
            
            # Personalizar un poco cada plan
            plan_data.learning_path.phases[0].name = f"Fase {i+1}"
            plan_data.learning_path.phases[0].atoms = [f"atom_{i+1}"]
            plan_data.agent_metadata.reasoning_steps = [f"Plan {i+1} created for testing"]
            
            await repository.save(plan_data)
            plan_ids.append(plan_data.plan_id)
            print(f"✅ Plan {i+1} creado: {plan_data.plan_id}")
        
        # Recuperar todos los planes del usuario
        user_plans = await repository.get_user_plans(user_id)
        
        assert len(user_plans) >= 3
        
        # Verificar que todos nuestros planes están presentes
        found_ids = [p.plan_id for p in user_plans]
        for plan_id in plan_ids:
            assert plan_id in found_ids
        
        print(f"✅ Todos los planes recuperados correctamente")
        
        # Probar eliminar un plan
        deleted = await repository.delete(plan_ids[0])
        assert deleted == True
        print(f"✅ Plan eliminado correctamente")
        
        # Verificar que ya no existe
        deleted_plan = await repository.get(plan_ids[0])
        assert deleted_plan is None
        print(f"✅ Confirmado que el plan fue eliminado")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en test múltiple: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    # Permitir ejecutar el test directamente
    async def run_tests():
        try:
            await test_repository_basic_persistence()
            print("\n" + "="*50)
            await test_repository_multiple_plans()
            print("\n✅ Todos los tests completados exitosamente!")
        except Exception as e:
            print(f"\n❌ Error en los tests: {e}")
    
    asyncio.run(run_tests()) 