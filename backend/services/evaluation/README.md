# 🎯 Servicio Agéntico de Evaluación - Atomia

## 📋 Descripción

El Servicio Agéntico de Evaluación es un componente central del sistema educativo Atomia que utiliza razonamiento artificial avanzado para evaluar respuestas de estudiantes de manera adaptativa y pedagógicamente fundamentada.

## 🧠 Capacidades Agénticas

### Workflow Plan-Execute-Observe-Reflect
1. **PLAN**: Analiza la respuesta del estudiante y planifica estrategia de evaluación
2. **EXECUTE**: Aplica herramientas de evaluación especializadas
3. **OBSERVE**: Valida la calidad y completitud de la evaluación
4. **REFLECT**: Aplica principios pedagógicos para generar feedback constructivo

### Herramientas Educativas Especializadas
- `analyze_student_response`: Análisis semántico profundo de respuestas
- `detect_misconceptions`: Detección de conceptos erróneos comunes
- `generate_constructive_feedback`: Generación de retroalimentación pedagógica
- `calculate_learning_progress`: Cálculo de progreso de aprendizaje

### Principios Pedagógicos Implementados
- **Evaluación Formativa**: Feedback inmediato y constructivo
- **Scaffolding**: Apoyo graduado según nivel del estudiante
- **Zona de Desarrollo Próximo**: Retos ajustados al nivel actual
- **Metacognición**: Fomenta reflexión sobre el proceso de aprendizaje

## 🏗️ Arquitectura

```
evaluation/
├── src/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   ├── evaluation.py      # Endpoints de evaluación agéntica
│   │       │   └── health.py          # Health checks agénticos
│   │       └── router.py              # Router principal
│   ├── core/
│   │   ├── config.py                  # Configuración del servicio
│   │   ├── dependencies.py            # Inyección de dependencias
│   │   └── logging.py                 # Logging estructurado agéntico
│   ├── domain/
│   │   └── services/
│   │       └── agentic_evaluation_service.py  # Lógica de evaluación agéntica
│   ├── infrastructure/
│   │   ├── agentic/
│   │   │   └── orchestrator_client.py # Cliente del LLM Orchestrator
│   │   ├── database/
│   │   │   └── evaluation_repository.py # Repositorio de evaluaciones
│   │   └── cache/
│   │       └── redis_cache.py         # Cache de evaluaciones
│   ├── schemas.py                     # Modelos Pydantic agénticos
│   └── main.py                        # FastAPI application
├── requirements.txt                   # Dependencias agénticas
├── Dockerfile                         # Containerización
└── README.md                          # Esta documentación
```

## 🚀 Instalación y Ejecución

### Requisitos Previos
- Python 3.11+
- LLM Orchestrator ejecutándose en puerto 8002
- Redis (opcional, para cache)
- PostgreSQL (opcional, para persistencia)

### Instalación
```bash
cd backend/services/evaluation
pip install -r requirements.txt
```

### Ejecución
```bash
# Desarrollo
uvicorn src.main:app --reload --host 0.0.0.0 --port 8003

# Producción
uvicorn src.main:app --host 0.0.0.0 --port 8003 --workers 4
```

## 📡 API Endpoints

### Evaluación Agéntica
```http
POST /api/v1/evaluation/evaluate
Content-Type: application/json

{
  "question_id": "q123",
  "student_answer": "Una función lineal es...",
  "expected_concepts": ["pendiente", "ordenada", "proporcionalidad"],
  "difficulty_level": "intermedio",
  "user_id": "student_456",
  "context": {
    "previous_attempts": 2,
    "learning_path": "algebra_basics"
  }
}
```

### Respuesta
```json
{
  "evaluation_id": "eval_789",
  "score": 0.85,
  "feedback": {
    "strengths": ["Correcta identificación de componentes"],
    "improvements": ["Falta mencionar la proporcionalidad"],
    "suggestions": ["Revisa el concepto de tasa de cambio constante"]
  },
  "misconceptions_detected": [],
  "learning_progress": {
    "current_mastery": 0.75,
    "improvement": 0.15
  },
  "agent_metadata": {
    "reasoning_steps": [...],
    "tools_used": [...],
    "confidence_score": 0.92
  }
}
```

### Health Check Agéntico
```http
GET /api/v1/evaluation/health
```

### Capacidades Agénticas
```http
GET /api/v1/evaluation/agentic-capabilities
```

## 🔧 Configuración

### Variables de Entorno
```env
# LLM Orchestrator
LLM_ORCHESTRATOR_URL=http://localhost:8002
LLM_ORCHESTRATOR_TIMEOUT=30

# Base de Datos
DATABASE_URL=postgresql://user:password@localhost/atomia_evaluation

# Redis Cache
REDIS_URL=redis://localhost:6379/1

# Configuración Agéntica
MAX_REASONING_ITERATIONS=10
EVALUATION_CONFIDENCE_THRESHOLD=0.8
ENABLE_MISCONCEPTION_DETECTION=true
```

## 🧪 Testing

```bash
# Tests unitarios
pytest tests/unit

# Tests de integración agéntica
pytest tests/integration

# Test del workflow completo
python test_agentic_evaluation.py
```

## 📊 Métricas y Monitoreo

### Métricas Agénticas
- `evaluation_reasoning_duration`: Tiempo de razonamiento del agente
- `evaluation_tools_usage`: Uso de herramientas educativas
- `evaluation_confidence_score`: Confianza en la evaluación
- `misconceptions_detected_count`: Conceptos erróneos detectados

## 🔍 Logging Estructurado

```json
{
  "timestamp": "2024-01-15T10:30:45Z",
  "service": "evaluation",
  "operation": "agentic_evaluation",
  "user_id": "student_456",
  "question_id": "q123",
  "reasoning_steps": 4,
  "tools_used": ["analyze_response", "detect_misconceptions"],
  "confidence": 0.92,
  "duration_ms": 1250
}
```

## 🤝 Integración con Otros Servicios

- **Atomization Service**: Obtiene información sobre átomos evaluados
- **Planning Service**: Actualiza rutas de aprendizaje basadas en evaluaciones
- **Questions Service**: Retroalimenta la generación de preguntas adaptativas
- **Gamification Service**: Proporciona datos para recompensas y logros

## 📚 Documentación Adicional

- [Principios de Evaluación Adaptativa](../../docs/evaluacion/evaluacion_adaptativa.md)
- [Sistema de Evaluación de Respuestas](../../docs/evaluacion/Sistema%20de%20Evaluación%20de%20Respuestas%20del%20Usuario.md)
- [Integración con LLM](../../development/llm-integration.md)

---

*Servicio Agéntico de Evaluación - Parte del Sistema Educativo Atomia* 