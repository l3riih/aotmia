#!/usr/bin/env python3
"""
Script de verificación de conectividad de bases de datos para Atomia
Verifica PostgreSQL, MongoDB y Redis
"""

import asyncio
import asyncpg
import redis
import pymongo
from datetime import datetime
import sys
import os

# Colores para output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
ENDC = '\033[0m'

def print_status(service: str, status: str, details: str = ""):
    color = GREEN if status == "✓" else RED if status == "✗" else YELLOW
    print(f"{color}{status}{ENDC} {service}: {details}")

async def test_postgresql():
    """Prueba conectividad a PostgreSQL"""
    try:
        # Configuración desde el servicio de evaluación
        conn = await asyncpg.connect(
            host="localhost",
            port=5432,
            database="atomia_evaluation",
            user="atomia",
            password="atomia_password"
        )
        
        # Verificar que podemos ejecutar consultas
        version = await conn.fetchval("SELECT version()")
        await conn.close()
        
        print_status("PostgreSQL", "✓", f"Conectado - {version.split(',')[0]}")
        return True
        
    except Exception as e:
        print_status("PostgreSQL", "✗", f"Error: {str(e)}")
        return False

def test_mongodb():
    """Prueba conectividad a MongoDB"""
    try:
        # Configuración desde el servicio de atomización
        client = pymongo.MongoClient("mongodb://localhost:27017")
        
        # Verificar conexión
        server_info = client.server_info()
        
        # Acceder a la base de datos de atomización
        db = client.atomia_atomization
        
        # Insertar y leer un documento de prueba
        test_collection = db.test_connection
        test_doc = {"test": True, "timestamp": datetime.now()}
        result = test_collection.insert_one(test_doc)
        
        # Verificar que se insertó
        found = test_collection.find_one({"_id": result.inserted_id})
        
        # Limpiar documento de prueba
        test_collection.delete_one({"_id": result.inserted_id})
        
        client.close()
        
        print_status("MongoDB", "✓", f"Conectado - v{server_info['version']}")
        return True
        
    except Exception as e:
        print_status("MongoDB", "✗", f"Error: {str(e)}")
        return False

def test_redis():
    """Prueba conectividad a Redis"""
    try:
        # Configuración desde el LLM orchestrator
        r = redis.Redis(host="localhost", port=6379, db=0)
        
        # Verificar conexión con ping
        r.ping()
        
        # Prueba de escritura/lectura
        test_key = "atomia:test:connection"
        test_value = f"test_{datetime.now().isoformat()}"
        
        r.set(test_key, test_value, ex=10)  # TTL de 10 segundos
        retrieved = r.get(test_key)
        
        if retrieved and retrieved.decode() == test_value:
            # Obtener información del servidor
            info = r.info()
            redis_version = info.get('redis_version', 'unknown')
            
            print_status("Redis", "✓", f"Conectado - v{redis_version}")
            return True
        else:
            raise Exception("No se pudo escribir/leer datos de prueba")
            
    except Exception as e:
        print_status("Redis", "✗", f"Error: {str(e)}")
        return False

async def test_all_databases():
    """Ejecuta todas las pruebas de conectividad"""
    print(f"{BLUE}=== Verificación de Conectividad de Bases de Datos - Atomia ==={ENDC}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    results = {}
    
    # PostgreSQL (async)
    results['postgresql'] = await test_postgresql()
    
    # MongoDB (sync)
    results['mongodb'] = test_mongodb()
    
    # Redis (sync)
    results['redis'] = test_redis()
    
    print()
    print(f"{BLUE}=== Resumen ==={ENDC}")
    
    all_good = all(results.values())
    
    if all_good:
        print_status("Sistema completo", "✓", "Todas las bases de datos están funcionando correctamente")
        print(f"\n{GREEN}🎉 ¡Sistema listo para ejecutar Atomia!{ENDC}")
        return True
    else:
        failed = [name for name, status in results.items() if not status]
        print_status("Sistema completo", "✗", f"Fallos en: {', '.join(failed)}")
        print(f"\n{RED}❌ Necesitas arreglar las conexiones antes de continuar{ENDC}")
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(test_all_databases())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{YELLOW}⚠️  Prueba interrumpida por el usuario{ENDC}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{RED}💥 Error inesperado: {str(e)}{ENDC}")
        sys.exit(1) 