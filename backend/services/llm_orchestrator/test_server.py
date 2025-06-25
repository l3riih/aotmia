#!/usr/bin/env python3
"""Script de prueba para el sistema agéntico."""

import sys
import asyncio
import json
import structlog
sys.path.append('.')

# Set up structured logging
structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

async def test_orchestrator():
    """Prueba básica del orquestador agéntico."""
    try:
        print("🚀 Iniciando prueba del sistema agéntico...")
        
        # Importar dependencias
        print("1. Importando configuración...")
        from src.config import config
        # FORZAR VALORES CORRECTOS PARA DEBUGGING
        config.azure_ai_model = "DeepSeek-R1"
        config.azure_ai_endpoint = "https://ai-bryanjavierjaramilloc0912ai799661901077.services.ai.azure.com/models"
        
        print(f"   ✅ Azure AI Endpoint (forzado): {config.azure_ai_endpoint}")
        print(f"   ✅ Modelo (forzado): {config.azure_ai_model}")
        
        print("2. Importando tipos de tarea...")
        from src.task_types import TaskType
        print(f"   ✅ Tipos disponibles: {list(TaskType)}")
        
        print("3. Importando orquestador...")
        from src.orchestrator import orchestrator
        print("   ✅ Orquestador cargado")
        
        print("4. Procesando tarea educativa de prueba...")
        result = await orchestrator.process(
            task_type=TaskType.CONTENT_EXPLANATION,
            user_input="¿Qué son las funciones matemáticas?",
            user_id="test_user_123",
            session_id="test_session_001"
        )
        
        print("🎉 ¡Resultado del sistema agéntico!")
        # Imprimir de forma segura, ya que el objeto puede no ser serializable
        print(f"Success: {result.get('success')}")
        print(f"Task Type: {result.get('task_type')}")
        print("Response:")
        print(result.get('response'))
        
        return result

    except Exception as e:
        print(f"❌ Error en prueba agéntica: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    result = asyncio.run(test_orchestrator())
    if result and result.get("success"):
        print("\n✅ Sistema agéntico funcionando correctamente!")
    else:
        print("\n❌ Hay problemas con el sistema agéntico") 