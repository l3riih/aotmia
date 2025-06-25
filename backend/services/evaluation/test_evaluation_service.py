#!/usr/bin/env python3
"""
Script de prueba para el Servicio Agéntico de Evaluación.
Prueba la integración completa con el LLM Orchestrator.
"""

import asyncio
import httpx
from typing import Dict, Any
import json
from datetime import datetime


class EvaluationTester:
    def __init__(self):
        self.base_url = "http://localhost:8003"
        self.client = httpx.AsyncClient(timeout=30.0)
        
    async def test_health(self):
        """Prueba el endpoint de health."""
        print("\n🔍 Probando Health Check...")
        response = await self.client.get(f"{self.base_url}/api/v1/evaluation/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    
    async def test_agentic_capabilities(self):
        """Prueba las capacidades agénticas."""
        print("\n🤖 Verificando Capacidades Agénticas...")
        response = await self.client.get(f"{self.base_url}/api/v1/evaluation/agentic-capabilities")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    
    async def test_evaluate_response(self):
        """Prueba la evaluación de una respuesta."""
        print("\n📝 Probando Evaluación de Respuesta...")
        
        # Datos de prueba
        evaluation_data = {
            "question_id": "math_001",
            "question_text": "¿Qué es una función lineal y cuáles son sus características principales?",
            "student_answer": "Una función lineal es una relación matemática donde cada valor de x corresponde a un único valor de y, y su gráfica es una línea recta. Sus características son: tiene la forma y = mx + b, donde m es la pendiente y b es la ordenada al origen.",
            "expected_concepts": ["función", "lineal", "pendiente", "ordenada", "gráfica", "recta"],
            "difficulty_level": "intermedio",
            "user_id": "test_student_123"
        }
        
        print(f"Enviando evaluación: {json.dumps(evaluation_data, indent=2)}")
        
        response = await self.client.post(
            f"{self.base_url}/api/v1/evaluation/evaluate",
            json=evaluation_data
        )
        
        print(f"\nStatus: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ Evaluación Exitosa!")
            print(f"ID: {result.get('evaluation_id')}")
            print(f"Score: {result.get('score')}")
            print(f"\nFeedback:")
            feedback = result.get('feedback', {})
            print(f"  - Fortalezas: {feedback.get('strengths')}")
            print(f"  - Mejoras: {feedback.get('improvements')}")
            print(f"  - Sugerencias: {feedback.get('suggestions')}")
            print(f"\nMisconceptions detectados: {result.get('misconceptions_detected')}")
            print(f"\nProgreso de aprendizaje:")
            progress = result.get('learning_progress', {})
            print(f"  - Dominio actual: {progress.get('current_mastery')}")
            print(f"  - Mejora: {progress.get('improvement')}")
            print(f"  - Tendencia: {progress.get('trend')}")
            print(f"\nMetadatos del Agente:")
            agent_meta = result.get('agent_metadata', {})
            print(f"  - Pasos de razonamiento: {len(agent_meta.get('reasoning_steps', []))}")
            print(f"  - Herramientas usadas: {agent_meta.get('tools_used')}")
            print(f"  - Confianza: {agent_meta.get('confidence_score')}")
        else:
            print(f"❌ Error: {response.text}")
        
        return response.status_code == 200
    
    async def test_batch_evaluate(self):
        """Prueba la evaluación por lotes."""
        print("\n📚 Probando Evaluación por Lotes...")
        
        batch_data = {
            "evaluations": [
                {
                    "question_id": "math_002",
                    "question_text": "¿Cuál es la derivada de f(x) = x²?",
                    "student_answer": "La derivada es 2x",
                    "expected_concepts": ["derivada", "función", "potencia"],
                    "difficulty_level": "intermedio",
                    "user_id": "test_student_123"
                },
                {
                    "question_id": "math_003",
                    "question_text": "¿Qué es el teorema de Pitágoras?",
                    "student_answer": "Es un teorema que dice que en un triángulo rectángulo, el cuadrado de la hipotenusa es igual a la suma de los cuadrados de los catetos: a² + b² = c²",
                    "expected_concepts": ["teorema", "Pitágoras", "triángulo", "rectángulo", "hipotenusa", "catetos"],
                    "difficulty_level": "básico",
                    "user_id": "test_student_123"
                }
            ]
        }
        
        response = await self.client.post(
            f"{self.base_url}/api/v1/evaluation/batch-evaluate",
            json=batch_data
        )
        
        print(f"\nStatus: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Evaluaciones procesadas: {result.get('processed')}")
            print(f"❌ Evaluaciones fallidas: {result.get('failed')}")
            
            for idx, evaluation in enumerate(result.get('results', [])):
                print(f"\nEvaluación {idx + 1}:")
                print(f"  - Score: {evaluation.get('score')}")
                print(f"  - Feedback: {evaluation.get('feedback', {}).get('strengths', [])[:1]}")
        else:
            print(f"❌ Error: {response.text}")
        
        return response.status_code == 200
    
    async def test_get_user_history(self):
        """Prueba obtener el historial de evaluaciones."""
        print("\n📊 Probando Historial de Usuario...")
        
        user_id = "test_student_123"
        response = await self.client.get(
            f"{self.base_url}/api/v1/evaluation/user/{user_id}/history"
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Total evaluaciones: {len(result.get('evaluations', []))}")
            print(f"Estadísticas: {json.dumps(result.get('statistics', {}), indent=2)}")
        else:
            print(f"❌ Error: {response.text}")
        
        return response.status_code == 200
    
    async def run_all_tests(self):
        """Ejecuta todas las pruebas."""
        print("🚀 Iniciando pruebas del Servicio Agéntico de Evaluación...")
        print("=" * 60)
        
        # Verificar que el servicio esté activo
        try:
            health_ok = await self.test_health()
            if not health_ok:
                print("\n❌ El servicio no está respondiendo correctamente")
                return
        except Exception as e:
            print(f"\n❌ Error conectando al servicio: {str(e)}")
            print("Asegúrate de que el servicio esté ejecutándose en http://localhost:8003")
            return
        
        # Ejecutar todas las pruebas
        tests = [
            self.test_agentic_capabilities,
            self.test_evaluate_response,
            self.test_batch_evaluate,
            self.test_get_user_history
        ]
        
        for test in tests:
            try:
                await test()
            except Exception as e:
                print(f"\n❌ Error en prueba {test.__name__}: {str(e)}")
        
        print("\n" + "=" * 60)
        print("✅ Pruebas completadas!")
    
    async def close(self):
        """Cierra el cliente HTTP."""
        await self.client.aclose()


async def main():
    """Función principal."""
    tester = EvaluationTester()
    try:
        await tester.run_all_tests()
    finally:
        await tester.close()


if __name__ == "__main__":
    print("\n📋 SERVICIO DE EVALUACIÓN AGÉNTICA - PRUEBAS")
    print("Asegúrate de tener ejecutándose:")
    print("1. LLM Orchestrator en http://localhost:8002")
    print("2. Servicio de Evaluación en http://localhost:8003")
    print("\nPresiona Enter para continuar...")
    input()
    
    asyncio.run(main()) 