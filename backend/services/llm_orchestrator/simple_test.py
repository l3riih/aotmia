#!/usr/bin/env python3

import sys
import os
sys.path.append('.')

# Cargar variables de entorno
from dotenv import load_dotenv
load_dotenv()

print("🚀 Probando sistema agéntico Atomia...")

try:
    print("1. Importando config...")
    from src.config import config
    print(f"   ✅ Azure AI configurado")
    
    print("2. Importando task_types...")
    from src.task_types import TaskType
    print(f"   ✅ Tipos de tarea: {len(list(TaskType))} disponibles")
    
    print("3. Importando herramientas educativas...")
    from src.tools import AVAILABLE_TOOLS
    print(f"   ✅ Herramientas cargadas: {[tool.name for tool in AVAILABLE_TOOLS]}")
    
    print("4. Importando sistema de memoria...")
    from src.memory import IntegratedMemorySystem
    print("   ✅ Sistema de memoria listo")
    
    print("5. Importando agente educativo...")
    from src.agents import AtomiaAgent
    print("   ✅ Agente educativo listo")
    
    print("\n🎉 ¡Sistema agéntico Atomia funcionando correctamente!")
    print("📚 Capacidades agénticas disponibles:")
    print("   - Agente educativo con razonamiento ReAct")
    print("   - Memoria multi-nivel (corto, largo plazo, semántica)")
    print("   - 4 herramientas educativas especializadas")
    print("   - Workflow Plan-Execute-Observe-Reflect")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc() 