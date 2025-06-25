# 📅 Servicio Agéntico de Planificación Adaptativa - Atomia

## 📋 Descripción

El Servicio Agéntico de Planificación es el cerebro estratégico del sistema educativo Atomia. Utiliza razonamiento artificial avanzado para crear y adaptar rutas de aprendizaje personalizadas basadas en el progreso, evaluaciones y características individuales de cada estudiante.

## 🧠 Capacidades Agénticas

### Workflow Plan-Execute-Observe-Reflect
1. **PLAN**: Analiza el estado actual del estudiante y define objetivos de aprendizaje
2. **EXECUTE**: Aplica algoritmos de planificación y herramientas de optimización
3. **OBSERVE**: Monitorea el progreso y valida la efectividad del plan
4. **REFLECT**: Ajusta la ruta basándose en resultados y feedback

### Herramientas Educativas Especializadas
- `analyze_learning_state`: Análisis del estado actual de aprendizaje
- `generate_learning_path`: Generación de rutas personalizadas
- `optimize_spaced_repetition`: Optimización de repetición espaciada
- `predict_learning_outcomes`: Predicción de resultados de aprendizaje
- `detect_learning_gaps`: Detección de brechas de conocimiento

### Algoritmos Pedagógicos Implementados
- **FSRS (Free Spaced Repetition Scheduler)**: Repetición espaciada optimizada
- **Zona de Desarrollo Próximo (ZDP)**: Ajuste dinámico de dificultad
- **Curva de Aprendizaje**: Modelado de progreso individual
- **Balanceo Exploración-Explotación**: Equilibrio entre nuevo contenido y repaso

## 🏗️ Arquitectura

```
planning/
├── src/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   ├── planning.py        # Endpoints de planificación
│   │       │   └── health.py          # Health checks
│   │       └── router.py              # Router principal
│   ├── core/
│   │   ├── config.py                  # Configuración
│   │   ├── dependencies.py            # Inyección de dependencias
│   │   └── logging.py                 # Logging estructurado
│   ├── domain/
│   │   └── services/
│   │       └── agentic_planning_service.py  # Lógica de planificación
│   ├── infrastructure/
│   │   ├── agentic/
│   │   │   └── orchestrator_client.py # Cliente LLM Orchestrator
│   │   ├── database/
│   │   │   └── planning_repository.py # Repositorio de planes
│   │   └── algorithms/
│   │       ├── fsrs.py                # Algoritmo FSRS
│   │       └── zdp.py                 # Zona Desarrollo Próximo
│   ├── schemas.py                     # Modelos Pydantic
│   └── main.py                        # FastAPI application
├── requirements.txt                   # Dependencias
├── Dockerfile                         # Containerización
└── README.md                          # Esta documentación
```

## 🚀 Instalación y Ejecución

### Requisitos Previos
- Python 3.11+
- LLM Orchestrator ejecutándose en puerto 8002
- Servicio de Atomización en puerto 8001
- Servicio de Evaluación en puerto 8003
- PostgreSQL (para persistencia de planes)

### Instalación
```bash
cd backend/services/planning
pip install -r requirements.txt
```

### Ejecución
```bash
# Desarrollo
uvicorn src.main:app --reload --host 0.0.0.0 --port 8004

# Producción
uvicorn src.main:app --host 0.0.0.0 --port 8004 --workers 4
```

## 📡 API Endpoints

### Crear Plan de Aprendizaje
```http
POST /api/v1/planning/create-plan
Content-Type: application/json

{
  "user_id": "student_123",
  "learning_goals": ["dominar funciones lineales"],
  "time_available_hours": 10,
  "preferred_difficulty": "intermedio",
  "context": {
    "current_level": "básico",
    "previous_topics": ["álgebra básica"],
    "learning_style": "visual"
  }
}
```

### Respuesta
```json
{
  "plan_id": "plan_abc123",
  "user_id": "student_123",
  "learning_path": {
    "total_atoms": 15,
    "estimated_time_hours": 8.5,
    "difficulty_progression": "gradual",
    "phases": [
      {
        "phase_id": 1,
        "name": "Fundamentos",
        "atoms": ["atom_1", "atom_2", "atom_3"],
        "estimated_duration_minutes": 90,
        "objectives": ["comprender concepto básico"]
      }
    ]
  },
  "schedule": {
    "daily_sessions": [
      {
        "day": 1,
        "atoms": ["atom_1", "atom_2"],
        "review_atoms": [],
        "estimated_time_minutes": 45
      }
    ]
  },
  "agent_metadata": {
    "reasoning_steps": [...],
    "tools_used": [...],
    "confidence_score": 0.89,
    "algorithms_applied": ["FSRS", "ZDP"]
  }
}
```

### Actualizar Plan Basado en Progreso
```http
PUT /api/v1/planning/update-plan/{plan_id}
Content-Type: application/json

{
  "completed_atoms": ["atom_1", "atom_2"],
  "evaluation_results": {
    "atom_1": {"score": 0.9, "time_spent_minutes": 20},
    "atom_2": {"score": 0.7, "time_spent_minutes": 30}
  },
  "user_feedback": "El contenido es muy denso"
}
```

### Obtener Recomendaciones Adaptativas
```http
GET /api/v1/planning/recommendations/{user_id}?context=current_session
```

### Health Check
```http
GET /api/v1/planning/health
```

## 🔧 Configuración

### Variables de Entorno
```env
# LLM Orchestrator
LLM_ORCHESTRATOR_URL=http://localhost:8002

# Base de Datos
DATABASE_URL=postgresql://user:password@localhost/atomia_planning

# Servicios Dependientes
ATOMIZATION_SERVICE_URL=http://localhost:8001
EVALUATION_SERVICE_URL=http://localhost:8003

# Algoritmos
FSRS_DEFAULT_PARAMETERS={"w": [0.4, 0.6, 2.4, 5.8]}
ZDP_DIFFICULTY_WINDOW=0.2
ENABLE_PREDICTIVE_MODELING=true

# Configuración Agéntica
MAX_PLANNING_ITERATIONS=15
MIN_CONFIDENCE_THRESHOLD=0.75
ENABLE_ADAPTIVE_REPLANNING=true
```

## 🧪 Testing

```bash
# Tests unitarios
pytest tests/unit

# Tests de algoritmos
pytest tests/algorithms

# Test del workflow agéntico
python test_agentic_planning.py
```

## 📊 Métricas y Monitoreo

### Métricas Agénticas
- `planning_generation_duration`: Tiempo de generación de planes
- `plan_adaptations_count`: Número de adaptaciones por plan
- `algorithm_usage`: Uso de cada algoritmo pedagógico
- `learning_path_effectiveness`: Efectividad de rutas generadas

## 🔍 Algoritmos Pedagógicos

### FSRS (Free Spaced Repetition Scheduler)
- Optimiza intervalos de repaso basados en dificultad y retención
- Parámetros adaptativos por estudiante
- Integración con evaluaciones para ajuste dinámico

### Zona de Desarrollo Próximo (ZDP)
- Mantiene el contenido en el nivel óptimo de desafío
- Ajusta dificultad basada en rendimiento
- Previene frustración y aburrimiento

### Balanceo Exploración-Explotación
- 70% consolidación de conocimientos actuales
- 30% exploración de nuevos conceptos
- Ajuste dinámico según progreso

## 🤝 Integración con Otros Servicios

- **Atomization Service**: Obtiene átomos disponibles y sus relaciones
- **Evaluation Service**: Recibe resultados para adaptar planes
- **Questions Service**: Coordina generación de preguntas según plan
- **Gamification Service**: Sincroniza recompensas con hitos del plan

## 📚 Documentación Adicional

- [Algoritmos de Planificación Adaptativa](../../docs/algoritmos/Algoritmos%20de%20Planificación%20Adaptativa%20de%20Aprendizaje.md)
- [Principios de Aprendizaje](../../docs/algoritmos/principios_aprendizaje.md)
- [Integración con LLM](../../development/llm-integration.md)

---

*Servicio Agéntico de Planificación - El cerebro estratégico de Atomia* 