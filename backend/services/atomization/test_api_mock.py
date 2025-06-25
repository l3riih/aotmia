#!/usr/bin/env python3
"""
Test del API del servicio de atomización agéntico con mock del LLM Orchestrator
"""

import asyncio
import json
from unittest.mock import patch, AsyncMock
import httpx

# Mock response del LLM Orchestrator
MOCK_AGENT_RESPONSE = {
    "answer": """
    ```json
    [
        {
            "id": "atom_1",
            "title": "Definición de Función Lineal",
            "content": "Una función lineal es una relación matemática donde cada entrada tiene una única salida, representada por la ecuación y = mx + b.",
            "difficulty": "intermedio",
            "prerequisites": [],
            "learning_objectives": ["Definir función lineal", "Identificar componentes m y b"],
            "estimated_time_minutes": 15,
            "tags": ["matemáticas", "álgebra", "funciones"]
        },
        {
            "id": "atom_2", 
            "title": "Componentes de la Función Lineal",
            "content": "En y = mx + b, 'm' representa la pendiente (qué tan inclinada está la línea) y 'b' representa la ordenada al origen (donde la línea cruza el eje y).",
            "difficulty": "intermedio",
            "prerequisites": ["atom_1"],
            "learning_objectives": ["Interpretar pendiente", "Interpretar ordenada al origen"],
            "estimated_time_minutes": 20,
            "tags": ["matemáticas", "álgebra", "pendiente"]
        }
    ]
    ```
    """,
    "reasoning_steps": [
        "PLAN: Analizar contenido sobre funciones lineales para identificar conceptos clave",
        "EXECUTE: Usar herramienta search_learning_atoms para validar estructura conceptual",
        "EXECUTE: Aplicar principios de microaprendizaje para dividir contenido en unidades coherentes",
        "OBSERVE: Verificar que cada átomo es autocontenido y evaluable",
        "REFLECT: Los átomos cumplen principios pedagógicos de Skinner - calidad satisfactoria"
    ],
    "tools_used": [
        "search_learning_atoms",
        "track_learning_progress", 
        "generate_adaptive_questions"
    ],
    "iterations": 3
}

async def mock_orchestrator_process(task_data):
    """Mock del proceso del orquestrador agéntico"""
    # Simular tiempo de procesamiento
    await asyncio.sleep(0.1)
    return MOCK_AGENT_RESPONSE

async def test_api_with_mock():
    """Test del API con mock del agente"""
    print("🧪 TESTING API DEL SERVICIO DE ATOMIZACIÓN AGÉNTICO")
    print("=" * 60)
    
    # Patchear el cliente del orquestrador agéntico
    with patch('src.infrastructure.agentic.orchestrator_client.AgenticOrchestratorClient.process_educational_task', new_callable=AsyncMock) as mock_process:
        mock_process.return_value = MOCK_AGENT_RESPONSE
        
        # Request de prueba
        test_request = {
            "content": "Las funciones lineales son relaciones matemáticas donde cada entrada tiene una única salida. Su forma general es y = mx + b, donde m es la pendiente y b es la ordenada al origen.",
            "objectives": "Enseñar conceptos básicos de funciones lineales",
            "difficulty_level": "intermedio",
            "user_id": "test_user_api"
        }
        
        print(f"📝 Enviando request al API...")
        print(f"🎯 Contenido: {len(test_request['content'])} caracteres")
        print(f"📊 Nivel: {test_request['difficulty_level']}")
        print(f"👤 Usuario: {test_request['user_id']}")
        
        # Hacer request al API
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    "http://localhost:8001/api/v1/atomization/atomize",
                    json=test_request,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    print(f"\n✅ REQUEST EXITOSO!")
                    print(f"📚 Átomos creados: {len(result.get('atoms', []))}")
                    print(f"🧠 Pasos de razonamiento: {len(result.get('reasoning_steps', []))}")
                    print(f"🛠️ Herramientas usadas: {len(result.get('tools_used', []))}")
                    print(f"🔄 Iteraciones: {result.get('iterations', 0)}")
                    print(f"⭐ Calidad: {result.get('quality_score', 0.0):.2f}")
                    
                    print(f"\n📚 DETALLES DE LOS ÁTOMOS:")
                    print("=" * 40)
                    for i, atom in enumerate(result.get('atoms', []), 1):
                        print(f"📖 Átomo {i}: {atom.get('title', 'Sin título')}")
                        print(f"   🎯 Objetivos: {len(atom.get('learning_objectives', []))}")
                        print(f"   ⏱️ Tiempo: {atom.get('estimated_time_minutes', 0)} min")
                        print(f"   🏷️ Tags: {', '.join(atom.get('tags', []))}")
                        print(f"   🤖 Creado por agente: {atom.get('created_by_agent', False)}")
                        print()
                    
                    print(f"🧠 METADATOS AGÉNTICOS:")
                    print("=" * 30)
                    agent_metadata = result.get('agent_metadata', {})
                    print(f"📋 Pasos de razonamiento: {len(agent_metadata.get('reasoning_steps', []))}")
                    print(f"🛠️ Herramientas utilizadas: {len(agent_metadata.get('tools_used', []))}")
                    print(f"🔄 Iteraciones del agente: {agent_metadata.get('iterations', 0)}")
                    
                    print(f"\n🧠 PASOS DE RAZONAMIENTO:")
                    for i, step in enumerate(result.get('reasoning_steps', []), 1):
                        print(f"   {i}. {step}")
                    
                    print(f"\n🛠️ HERRAMIENTAS UTILIZADAS:")
                    for tool in result.get('tools_used', []):
                        print(f"   • {tool}")
                    
                    print(f"\n🎉 ¡API DEL SERVICIO AGÉNTICO FUNCIONANDO PERFECTAMENTE!")
                    
                else:
                    print(f"❌ Error en API: {response.status_code}")
                    print(f"📄 Respuesta: {response.text}")
                    
            except Exception as e:
                print(f"❌ Error conectando al API: {str(e)}")

if __name__ == "__main__":
    print("🚀 Iniciando test del API con mock agéntico...")
    asyncio.run(test_api_with_mock()) 