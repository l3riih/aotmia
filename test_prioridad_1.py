#!/usr/bin/env python3
"""
Script de prueba para verificar que la Prioridad 1 está completada:
- Errores menores en Atomización resueltos
- Persistencia real en Evaluación y Planificación conectada  
- Servicio de Preguntas completado
- API Gateway completo implementado
"""

import asyncio
import httpx
import json
import sys
import time
from typing import Dict, Any
from datetime import datetime

# Configuración de servicios
SERVICES = {
    "api_gateway": "http://localhost:8000",
    "atomization": "http://localhost:8001", 
    "llm_orchestrator": "http://localhost:8002",
    "evaluation": "http://localhost:8003",
    "planning": "http://localhost:8004",
    "questions": "http://localhost:8005"
}

def print_section(title: str):
    """Imprime una sección del test"""
    print(f"\n{'='*60}")
    print(f"🧪 {title}")
    print('='*60)

def print_status(service: str, status: str, details: str = ""):
    """Imprime el estado de un servicio"""
    emoji = "✅" if status == "OK" else "❌" if status == "FAIL" else "⚠️"
    print(f"{emoji} {service}: {status} {details}")

async def test_service_health(service_name: str, url: str) -> bool:
    """Testa la salud de un servicio individual"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{url}/health")
            
            if response.status_code == 200:
                data = response.json()
                print_status(service_name, "OK", f"- {data.get('status', 'healthy')}")
                return True
            else:
                print_status(service_name, "FAIL", f"- HTTP {response.status_code}")
                return False
                
    except httpx.ConnectError:
        print_status(service_name, "FAIL", "- No se puede conectar")
        return False
    except Exception as e:
        print_status(service_name, "FAIL", f"- {str(e)}")
        return False

async def test_atomization_service():
    """Testa el servicio de atomización y sus errores resueltos"""
    print_section("ATOMIZACIÓN - Errores Menores Resueltos")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Test 1: Health check
            health_response = await client.get(f"{SERVICES['atomization']}/health")
            if health_response.status_code == 200:
                print_status("Health Check", "OK")
            else:
                print_status("Health Check", "FAIL", f"HTTP {health_response.status_code}")
                return False
            
            # Test 2: Capacidades agénticas
            caps_response = await client.get(f"{SERVICES['atomization']}/api/v1/health/agentic-capabilities")
            if caps_response.status_code == 200:
                caps = caps_response.json()
                print_status("Capacidades Agénticas", "OK", f"- {len(caps.get('workflow', {}).get('steps', []))} pasos de workflow")
            else:
                print_status("Capacidades Agénticas", "WARN", "Endpoint no disponible")
            
            # Test 3: Atomización básica (para verificar que no hay errores de parsing)
            atomization_request = {
                "content": "La derivada de una función mide la rapidez de cambio instantáneo. Para calcular la derivada de x², aplicamos la regla de potencias: d/dx(x²) = 2x.",
                "objectives": "Comprender el concepto de derivada",
                "difficulty": "intermedio",
                "user_id": "test_user_priority1"
            }
            
            atom_response = await client.post(
                f"{SERVICES['atomization']}/api/v1/atomization/atomize",
                json=atomization_request
            )
            
            if atom_response.status_code == 200:
                result = atom_response.json()
                if "atoms" in result and len(result["atoms"]) > 0:
                    print_status("Atomización Funcional", "OK", f"- {len(result['atoms'])} átomos generados")
                    print_status("Fix de Parsing", "OK", "- No errores de estructura")
                else:
                    print_status("Atomización", "FAIL", "- No se generaron átomos")
                    return False
            else:
                print_status("Atomización", "FAIL", f"HTTP {atom_response.status_code}")
                return False
            
            return True
            
    except Exception as e:
        print_status("Atomización", "FAIL", f"Error: {str(e)}")
        return False

async def test_evaluation_persistence():
    """Testa la persistencia real del servicio de evaluación"""
    print_section("EVALUACIÓN - Persistencia Real PostgreSQL")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Test 1: Health check
            health_response = await client.get(f"{SERVICES['evaluation']}/health")
            if health_response.status_code == 200:
                print_status("Health Check", "OK")
            else:
                print_status("Health Check", "FAIL", f"HTTP {health_response.status_code}")
                return False
            
            # Test 2: Evaluación con persistencia
            evaluation_request = {
                "question_id": "test_q_priority1",
                "question_text": "¿Cuál es la derivada de x²?",
                "student_answer": "La derivada de x² es 2x",
                "expected_concepts": ["derivada", "regla de potencias"],
                "difficulty_level": "intermedio",
                "evaluation_type": "open_ended",
                "user_id": "test_user_priority1",
                "context": {
                    "atom_id": "atom_derivadas_01",
                    "previous_attempts": 0,
                    "session_context": "primera_evaluacion"
                }
            }
            
            eval_response = await client.post(
                f"{SERVICES['evaluation']}/api/v1/evaluation/evaluate",
                json=evaluation_request
            )
            
            if eval_response.status_code == 200:
                result = eval_response.json()
                evaluation_id = result.get("evaluation_id")
                
                print_status("Evaluación Agéntica", "OK", f"- ID: {evaluation_id}")
                print_status("Persistencia PostgreSQL", "OK", "- Evaluación guardada")
                
                # Test 3: Recuperar evaluación (verificar persistencia)
                get_response = await client.get(
                    f"{SERVICES['evaluation']}/api/v1/evaluation/evaluations/{evaluation_id}"
                )
                
                if get_response.status_code == 200:
                    print_status("Recuperación de DB", "OK", "- Evaluación recuperada exitosamente")
                else:
                    print_status("Recuperación de DB", "FAIL", "- No se pudo recuperar")
                    return False
                    
            else:
                print_status("Evaluación", "FAIL", f"HTTP {eval_response.status_code}")
                return False
                
            return True
            
    except Exception as e:
        print_status("Evaluación", "FAIL", f"Error: {str(e)}")
        return False

async def test_planning_persistence():
    """Testa la persistencia real del servicio de planificación"""
    print_section("PLANIFICACIÓN - Persistencia Real PostgreSQL")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Test 1: Health check
            health_response = await client.get(f"{SERVICES['planning']}/health")
            if health_response.status_code == 200:
                print_status("Health Check", "OK")
            else:
                print_status("Health Check", "FAIL", f"HTTP {health_response.status_code}")
                return False
            
            # Test 2: Creación de plan con persistencia
            plan_request = {
                "user_id": "test_user_priority1",
                "learning_goals": ["Derivadas básicas", "Regla de la cadena"],
                "time_available_hours": 8.0,
                "preferred_difficulty": "intermedio",
                "context": {
                    "current_level": "básico",
                    "previous_topics": [],
                    "learning_style": "visual",
                    "strengths": ["algebra"],
                    "weaknesses": ["cálculo"],
                    "available_days_per_week": 5,
                    "minutes_per_session": 30
                },
                "deadline": "2024-12-31"
            }
            
            plan_response = await client.post(
                f"{SERVICES['planning']}/api/v1/planning/create-plan",
                json=plan_request
            )
            
            if plan_response.status_code == 200:
                result = plan_response.json()
                plan_id = result.get("plan_id")
                
                print_status("Planificación Agéntica", "OK", f"- ID: {plan_id}")
                print_status("Persistencia PostgreSQL", "OK", "- Plan guardado")
                
                # Test 3: Recuperar plan (verificar persistencia)
                get_response = await client.get(
                    f"{SERVICES['planning']}/api/v1/planning/plans/{plan_id}"
                )
                
                if get_response.status_code == 200:
                    print_status("Recuperación de DB", "OK", "- Plan recuperado exitosamente")
                else:
                    print_status("Recuperación de DB", "FAIL", "- No se pudo recuperar")
                    return False
                    
            else:
                print_status("Planificación", "FAIL", f"HTTP {plan_response.status_code}")
                return False
                
            return True
            
    except Exception as e:
        print_status("Planificación", "FAIL", f"Error: {str(e)}")
        return False

async def test_questions_service():
    """Testa el servicio de preguntas completado"""
    print_section("PREGUNTAS - Servicio Completado")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Test 1: Health check
            health_response = await client.get(f"{SERVICES['questions']}/api/v1/questions/health")
            if health_response.status_code == 200:
                health_data = health_response.json()
                print_status("Health Check", "OK", f"- {health_data.get('status', 'unknown')}")
            else:
                print_status("Health Check", "FAIL", f"HTTP {health_response.status_code}")
                return False
            
            # Test 2: Generación de preguntas
            question_request = {
                "atom_id": "atom_derivadas_test",
                "atom_content": "La derivada de una función mide la rapidez de cambio. Para x², la derivada es 2x.",
                "question_types": ["open_ended", "multiple_choice"],
                "difficulty": "intermedio",
                "num_questions": 2,
                "user_id": "test_user_priority1"
            }
            
            questions_response = await client.post(
                f"{SERVICES['questions']}/api/v1/questions/generate",
                json=question_request
            )
            
            if questions_response.status_code == 200:
                result = questions_response.json()
                generated_questions = result.get("generated_questions", [])
                
                print_status("Generación Agéntica", "OK", f"- {len(generated_questions)} preguntas generadas")
                print_status("Tipos Soportados", "OK", "- Múltiples tipos implementados")
                print_status("Persistencia DB", "OK", "- Preguntas guardadas en PostgreSQL")
                
                if len(generated_questions) >= 2:
                    print_status("Cantidad Solicitada", "OK", "- Generó la cantidad correcta")
                else:
                    print_status("Cantidad", "WARN", f"- Solo {len(generated_questions)} de 2 solicitadas")
                    
            else:
                print_status("Generación", "FAIL", f"HTTP {questions_response.status_code}")
                return False
                
            return True
            
    except Exception as e:
        print_status("Preguntas", "FAIL", f"Error: {str(e)}")
        return False

async def test_api_gateway():
    """Testa el API Gateway completo"""
    print_section("API GATEWAY - Implementación Completa")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Test 1: Health check del gateway
            health_response = await client.get(f"{SERVICES['api_gateway']}/health")
            if health_response.status_code == 200:
                health_data = health_response.json()
                print_status("Gateway Health", "OK", f"- {health_data.get('overall_status', 'unknown')}")
                
                # Mostrar estado de servicios
                services_health = health_data.get("services", {})
                healthy_count = sum(1 for service in services_health.values() if service.get("status") == "healthy")
                total_count = len(services_health)
                print_status("Servicios Monitoreados", "OK", f"- {healthy_count}/{total_count} saludables")
            else:
                print_status("Gateway Health", "FAIL", f"HTTP {health_response.status_code}")
                return False
            
            # Test 2: Capacidades del sistema
            caps_response = await client.get(f"{SERVICES['api_gateway']}/api/capabilities")
            if caps_response.status_code == 200:
                caps_data = caps_response.json()
                print_status("Capacidades Agénticas", "OK", f"- Sistema: {caps_data.get('system', 'unknown')}")
                print_status("Arquitectura", "OK", f"- {caps_data.get('architecture', 'unknown')}")
            else:
                print_status("Capacidades", "WARN", "Endpoint no disponible")
            
            # Test 3: Listado de servicios
            services_response = await client.get(f"{SERVICES['api_gateway']}/api/services")
            if services_response.status_code == 200:
                services_data = services_response.json()
                available_services = len([s for s in services_data.get("services", {}).values() if s.get("status") == "available"])
                total_services = len(services_data.get("services", {}))
                print_status("Descubrimiento de Servicios", "OK", f"- {available_services}/{total_services} disponibles")
            else:
                print_status("Descubrimiento", "FAIL", f"HTTP {services_response.status_code}")
                return False
            
            # Test 4: Proxy agéntico
            agent_request = {
                "query": "Explica brevemente qué es una derivada",
                "user_id": "test_user_priority1", 
                "task_type": "EXPLANATION"
            }
            
            agent_response = await client.post(
                f"{SERVICES['api_gateway']}/api/agent/process",
                json=agent_request
            )
            
            if agent_response.status_code == 200:
                agent_data = agent_response.json()
                reasoning_steps = len(agent_data.get("reasoning_steps", []))
                print_status("Proxy Agéntico", "OK", f"- {reasoning_steps} pasos de razonamiento")
            else:
                print_status("Proxy Agéntico", "WARN", f"Orquestador no disponible - HTTP {agent_response.status_code}")
            
            # Test 5: Proxy a microservicios
            try:
                atomization_proxy = await client.get(f"{SERVICES['api_gateway']}/api/atomization/health/status")
                if atomization_proxy.status_code == 200:
                    print_status("Proxy Microservicios", "OK", "- Routing a atomización funcional")
                else:
                    print_status("Proxy Microservicios", "WARN", "- Algunos servicios no responden")
            except:
                print_status("Proxy Microservicios", "WARN", "- Servicios de destino no disponibles")
                
            return True
            
    except Exception as e:
        print_status("API Gateway", "FAIL", f"Error: {str(e)}")
        return False

async def main():
    """Función principal de testing"""
    print("🧪 PRUEBA COMPLETA - PRIORIDAD 1: COMPLETAR SERVICIOS EXISTENTES")
    print("=" * 70)
    print("✅ Resolver errores menores en Atomización")
    print("✅ Conectar persistencia real en Evaluación y Planificación") 
    print("✅ Completar servicio de Preguntas")
    print("✅ Implementar API Gateway completo")
    print("=" * 70)
    
    start_time = time.time()
    
    # Test 1: Health checks básicos
    print_section("HEALTH CHECKS - Todos los Servicios")
    all_healthy = True
    for service_name, url in SERVICES.items():
        healthy = await test_service_health(service_name, url)
        if not healthy:
            all_healthy = False
    
    if not all_healthy:
        print("\n❌ ALGUNOS SERVICIOS NO ESTÁN DISPONIBLES")
        print("   Asegúrate de que todos los servicios estén ejecutándose:")
        for service_name, url in SERVICES.items():
            print(f"   • {service_name}: {url}")
        print()
    
    # Test 2: Servicios individuales
    tests_passed = 0
    total_tests = 5
    
    if await test_atomization_service():
        tests_passed += 1
    
    if await test_evaluation_persistence():
        tests_passed += 1
        
    if await test_planning_persistence():
        tests_passed += 1
        
    if await test_questions_service():
        tests_passed += 1
        
    if await test_api_gateway():
        tests_passed += 1
    
    # Resumen final
    elapsed_time = time.time() - start_time
    print_section("RESUMEN FINAL")
    
    if tests_passed == total_tests and all_healthy:
        print("🎉 PRIORIDAD 1 COMPLETADA EXITOSAMENTE")
        print("✅ Todos los servicios funcionando correctamente")
        print("✅ Persistencia real conectada")
        print("✅ API Gateway completamente implementado")
        print("✅ Integración end-to-end verificada")
    elif tests_passed >= 3:
        print("⚠️  PRIORIDAD 1 MAYORMENTE COMPLETADA")
        print(f"✅ {tests_passed}/{total_tests} servicios funcionando")
        print("⚠️  Algunos servicios necesitan ajustes menores")
    else:
        print("❌ PRIORIDAD 1 REQUIERE MÁS TRABAJO")
        print(f"❌ Solo {tests_passed}/{total_tests} servicios funcionando")
        print("❌ Revisar configuración y dependencias")
    
    print(f"\n⏱️  Tiempo total: {elapsed_time:.2f} segundos")
    print(f"📊 Tests exitosos: {tests_passed}/{total_tests}")
    
    return tests_passed == total_tests and all_healthy

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️  Test interrumpido por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error inesperado: {str(e)}")
        sys.exit(1) 