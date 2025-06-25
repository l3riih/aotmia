#!/usr/bin/env python3

import sys
import os
sys.path.append('.')

print("🔍 Debug del sistema agéntico Atomia")
print("=" * 50)

try:
    print("✓ Python executable:", sys.executable)
    print("✓ Working directory:", os.getcwd())
    print()
    
    print("Paso 1: Cargando variables de entorno...")
    from dotenv import load_dotenv
    result = load_dotenv()
    print(f"✓ .env cargado: {result}")
    print(f"✓ AZURE_AI_KEY presente: {'AZURE_AI_KEY' in os.environ}")
    print()
    
    print("Paso 2: Importando configuración...")
    from src.config import config
    print(f"✓ Config cargada")
    print(f"  - Endpoint: {config.azure_ai_endpoint[:50]}...")
    print(f"  - Modelo: {config.azure_ai_model}")
    print()
    
    print("Paso 3: Verificando conexión a Redis...")
    import redis
    r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    r.ping()
    print("✓ Redis/Valkey conectado")
    print()
    
    print("Paso 4: Verificando LangChain...")
    from langchain.llms.base import BaseLLM
    print("✓ LangChain importado")
    print()
    
    print("Paso 5: Verificando ChromaDB...")
    import chromadb
    print("✓ ChromaDB importado")
    print()
    
    print("🎉 Todas las dependencias básicas funcionan!")
    print("El sistema agéntico está listo para funcionar.")
    
except Exception as e:
    print(f"❌ Error en: {e}")
    import traceback
    traceback.print_exc() 