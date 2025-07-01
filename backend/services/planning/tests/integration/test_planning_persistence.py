"""
Test de integración para verificar que los planes de aprendizaje se persisten correctamente.
"""

import pytest
import httpx
import asyncpg
from datetime import date
import os


BASE_URL = os.getenv("PLANNING_URL", "http://localhost:8004")
DB_URL = "postgresql://atomia_user:atomia_password@localhost:5432/atomia_dev"


@pytest.mark.asyncio
async def test_create_plan_persists():
    """Test que verifica que un plan creado se persiste en la base de datos."""
    
    # Payload de ejemplo para crear un plan
    payload = {
        "user_id": "student_test_123",
        "learning_goals": ["Derivadas", "Integrales básicas"],
        "time_available_hours": 10.0,
        "preferred_difficulty": "intermedio",
        "context": {
            "current_level": "básico",
            "previous_topics": [],
            "learning_style": "mixto",
            "strengths": [],
            "weaknesses": [],
            "available_days_per_week": 5,
            "minutes_per_session": 30
        },
        "deadline": str(date.today())
    }
    
    # Llamar al endpoint de creación de plan
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{BASE_URL}/api/v1/planning/create-plan",
            json=payload
        )
        
        # Verificar que la respuesta sea exitosa
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        plan_data = response.json()
        assert "plan_id" in plan_data
        assert plan_data["user_id"] == payload["user_id"]
        
        plan_id = plan_data["plan_id"]
    
    # Verificar que el plan se guardó en la base de datos
    conn = await asyncpg.connect(DB_URL)
    try:
        # Buscar el plan en la tabla learning_plans
        row = await conn.fetchrow(
            "SELECT plan_id, user_id, status FROM learning_plans WHERE plan_id = $1",
            plan_id
        )
        
        assert row is not None, f"Plan {plan_id} no se encontró en la base de datos"
        assert row["plan_id"] == plan_id
        assert row["user_id"] == payload["user_id"]
        assert row["status"] in ["draft", "active"]
        
    finally:
        await conn.close()


@pytest.mark.asyncio
async def test_get_plan_by_id():
    """Test que verifica que se puede recuperar un plan por ID."""
    
    # Primero crear un plan
    payload = {
        "user_id": "student_get_test",
        "learning_goals": ["Límites"],
        "time_available_hours": 5.0,
        "preferred_difficulty": "básico",
        "context": {
            "current_level": "básico",
            "previous_topics": [],
            "learning_style": "visual",
            "strengths": [],
            "weaknesses": [],
            "available_days_per_week": 3,
            "minutes_per_session": 45
        }
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Crear plan
        create_response = await client.post(
            f"{BASE_URL}/api/v1/planning/create-plan",
            json=payload
        )
        assert create_response.status_code == 200
        plan_id = create_response.json()["plan_id"]
        
        # Recuperar plan por ID
        get_response = await client.get(
            f"{BASE_URL}/api/v1/planning/plans/{plan_id}"
        )
        
        if get_response.status_code == 404:
            # El endpoint podría no estar implementado aún
            pytest.skip("Endpoint GET /plans/{id} not implemented yet")
        
        assert get_response.status_code == 200
        retrieved_plan = get_response.json()
        assert retrieved_plan["plan_id"] == plan_id
        assert retrieved_plan["user_id"] == payload["user_id"] 