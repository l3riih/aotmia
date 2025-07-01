"""
Test de persistencia directo - Sin HTTP, usando clases directamente
"""

import pytest
import asyncio
from datetime import date, datetime
from uuid import uuid4

from src.domain.services.agentic_planning_service import AgenticPlanningService
from src.infrastructure.database.planning_repository import PostgresPlanningRepository
from src.infrastructure.agentic.orchestrator_client import OrchestratorClient
from src.infrastructure.clients.atomization_client import AtomizationClient
from src.infrastructure.clients.evaluation_client import EvaluationClient
from src.schemas import CreatePlanRequest, LearningContext

# Configurar la conexión a la base de datos para testing
TEST_DATABASE_URL = "postgresql://user:password@localhost/atomia_planning"


@pytest.fixture
async def planning_service():
    """Fixture que crea una instancia del servicio de planning con dependencias reales"""
    # Crear instancias de los clientes (con fallback si no están disponibles)
    orchestrator_client = OrchestratorClient("http://localhost:8002")
    atomization_client = AtomizationClient("http://localhost:8001")
    evaluation_client = EvaluationClient("http://localhost:8003")
    
    # Crear el repositorio con la base de datos real
    repository = PostgresPlanningRepository(TEST_DATABASE_URL)
    
    # Inicializar el repositorio
    await repository.initialize()
    
    # Crear el servicio agéntico
    service = AgenticPlanningService(
        agentic_orchestrator=orchestrator_client,
        repository=repository,
        atomization_client=atomization_client,
        evaluation_client=evaluation_client
    )
    
    yield service
    
    # Cleanup - cerrar conexiones
    await repository.close()


# Función helper para crear el servicio de forma simple
async def create_planning_service():
    """Crear una instancia del servicio de planning"""
    orchestrator_client = OrchestratorClient("http://localhost:8002")
    atomization_client = AtomizationClient("http://localhost:8001")
    evaluation_client = EvaluationClient("http://localhost:8003")
    
    repository = PostgresPlanningRepository(TEST_DATABASE_URL)
    await repository.initialize()
    
    service = AgenticPlanningService(
        agentic_orchestrator=orchestrator_client,
        repository=repository,
        atomization_client=atomization_client,
        evaluation_client=evaluation_client
    )
    
    return service, repository


@pytest.mark.asyncio
async def test_direct_plan_creation_and_persistence():
    """Test que verifica la creación y persistencia de un plan directamente"""
    
    # Crear el servicio
    planning_service, repository = await create_planning_service()
    
    try:
        # Crear request de plan
        plan_request = CreatePlanRequest(
            user_id="test_user_direct_123",
            learning_goals=["Derivadas", "Integrales básicas"],
            time_available_hours=10.0,
            preferred_difficulty="intermedio",
            context=LearningContext(
                current_level="básico",
                previous_topics=[],
                learning_style="mixto",
                strengths=[],
                weaknesses=[],
                available_days_per_week=5,
                minutes_per_session=30
            ),
            deadline=date.today()
        )
        
        # Crear el plan usando el servicio
        plan_result = await planning_service.create_plan(plan_request)
    
    # Verificar que el plan fue creado exitosamente
    assert plan_result is not None
    assert "plan_id" in plan_result
    assert "status" in plan_result
    
    plan_id = plan_result["plan_id"]
    print(f"✅ Plan creado con ID: {plan_id}")
    
    # Verificar que el plan se persistió en la base de datos
    saved_plan = await planning_service.get_plan_by_id(plan_id)
    
    assert saved_plan is not None
    assert saved_plan["id"] == plan_id
    assert saved_plan["user_id"] == "test_user_direct_123"
    assert saved_plan["learning_goals"] == ["Derivadas", "Integrales básicas"]
    assert saved_plan["status"] in ["active", "draft", "created"]
    
        print(f"✅ Plan recuperado exitosamente desde la base de datos")
        print(f"   - Status: {saved_plan['status']}")
        print(f"   - Goals: {saved_plan['learning_goals']}")
        print(f"   - User: {saved_plan['user_id']}")
        
        return saved_plan
    
    finally:
        # Cleanup
        await repository.close()


@pytest.mark.asyncio
async def test_direct_plan_update_persistence(planning_service):
    """Test que verifica la actualización de estado de un plan"""
    
    # Primero crear un plan
    plan_request = CreatePlanRequest(
        user_id="test_user_update_456",
        learning_goals=["Límites"],
        time_available_hours=5.0,
        preferred_difficulty="básico",
        context=LearningContext(
            current_level="básico",
            previous_topics=[],
            learning_style="visual",
            strengths=[],
            weaknesses=[],
            available_days_per_week=3,
            minutes_per_session=45
        )
    )
    
    plan_result = await planning_service.create_plan(plan_request)
    plan_id = plan_result["plan_id"]
    
    print(f"✅ Plan inicial creado: {plan_id}")
    
    # Actualizar el estado del plan
    update_result = await planning_service.update_plan_status(plan_id, "in_progress")
    
    assert update_result is not None
    assert update_result["status"] == "in_progress"
    
    print(f"✅ Plan actualizado a 'in_progress'")
    
    # Verificar que la actualización se persistió
    updated_plan = await planning_service.get_plan_by_id(plan_id)
    
    assert updated_plan["status"] == "in_progress"
    assert updated_plan["updated_at"] is not None
    
    print(f"✅ Actualización persistida correctamente")
    
    return updated_plan


@pytest.mark.asyncio
async def test_direct_user_plans_retrieval(planning_service):
    """Test que verifica la recuperación de planes por usuario"""
    
    test_user_id = "test_user_multi_789"
    
    # Crear múltiples planes para el mismo usuario
    plan_requests = [
        CreatePlanRequest(
            user_id=test_user_id,
            learning_goals=["Matemáticas básicas"],
            time_available_hours=8.0,
            preferred_difficulty="básico",
            context=LearningContext(
                current_level="básico",
                previous_topics=[],
                learning_style="auditivo",
                strengths=[],
                weaknesses=[],
                available_days_per_week=4,
                minutes_per_session=30
            )
        ),
        CreatePlanRequest(
            user_id=test_user_id,
            learning_goals=["Física básica"],
            time_available_hours=12.0,
            preferred_difficulty="intermedio",
            context=LearningContext(
                current_level="intermedio",
                previous_topics=["Matemáticas básicas"],
                learning_style="kinestésico",
                strengths=["resolución de problemas"],
                weaknesses=[],
                available_days_per_week=5,
                minutes_per_session=45
            )
        )
    ]
    
    created_plan_ids = []
    
    # Crear los planes
    for i, plan_request in enumerate(plan_requests):
        plan_result = await planning_service.create_plan(plan_request)
        created_plan_ids.append(plan_result["plan_id"])
        print(f"✅ Plan {i+1} creado: {plan_result['plan_id']}")
    
    # Recuperar todos los planes del usuario
    user_plans = await planning_service.repository.get_user_plans(test_user_id)
    
    assert len(user_plans) >= 2  # Al menos los 2 que acabamos de crear
    
    # Verificar que nuestros planes están en la lista
    plan_ids_found = [plan["id"] for plan in user_plans]
    
    for plan_id in created_plan_ids:
        assert plan_id in plan_ids_found
    
    print(f"✅ Recuperados {len(user_plans)} planes para el usuario {test_user_id}")
    
    return user_plans


if __name__ == "__main__":
    # Permitir ejecutar el test directamente
    asyncio.run(test_direct_plan_creation_and_persistence()) 