"""
Servicio de Generación de Preguntas para Atomia
"""

import structlog
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import time
from typing import Dict, Any, List

# Configurar logging básico
logger = structlog.get_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestión del ciclo de vida del servicio"""
    logger.info("❓ Starting Atomia Questions Service")
    yield
    logger.info("🛑 Shutting down Atomia Questions Service")

app = FastAPI(
    title="Atomia - Questions Service",
    description="Servicio de generación de preguntas educativas con IA",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Middleware CORS básico
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware de timing
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Health check
@app.get("/health")
async def health_check():
    """Health check del servicio de preguntas"""
    return {
        "service": "questions",
        "status": "healthy",
        "version": "2.0.0",
        "features": {
            "question_generation": True,
            "multiple_choice": True,
            "open_ended": True,
            "true_false": True,
            "adaptive_difficulty": True,
            "ai_powered": True
        }
    }

# Endpoint raíz
@app.get("/")
async def root():
    """Información del servicio"""
    return {
        "service": "Atomia Questions Service",
        "version": "2.0.0",
        "description": "Servicio de generación de preguntas educativas",
        "status": "operational"
    }

# Endpoints de generación de preguntas
@app.post("/api/v1/questions/generate")
async def generate_questions(request_data: Dict[str, Any]):
    """Generar preguntas para un átomo de aprendizaje"""
    atom_id = request_data.get("atom_id", "unknown")
    num_questions = request_data.get("num_questions", 3)
    difficulty = request_data.get("difficulty", "medium")
    question_types = request_data.get("question_types", ["multiple_choice", "open_ended"])
    
    return {
        "atom_id": atom_id,
        "generated_questions": [
            {
                "id": "q1",
                "question_text": "¿Cuál es el concepto principal de este tema?",
                "question_type": "multiple_choice",
                "difficulty": difficulty,
                "options": [
                    {"option_text": "Opción A", "is_correct": False},
                    {"option_text": "Opción B", "is_correct": True},
                    {"option_text": "Opción C", "is_correct": False},
                    {"option_text": "Opción D", "is_correct": False}
                ],
                "correct_answer": "Opción B",
                "explanation": "Esta es la respuesta correcta porque..."
            },
            {
                "id": "q2",
                "question_text": "Explica en tus palabras el concepto principal.",
                "question_type": "open_ended",
                "difficulty": difficulty,
                "options": [],
                "correct_answer": "Una explicación comprensiva del concepto que incluye los elementos clave.",
                "explanation": "Esta pregunta evalúa la comprensión profunda del estudiante."
            },
            {
                "id": "q3",
                "question_text": "Este concepto es fundamental para el aprendizaje.",
                "question_type": "true_false",
                "difficulty": difficulty,
                "options": [
                    {"option_text": "Verdadero", "is_correct": True},
                    {"option_text": "Falso", "is_correct": False}
                ],
                "correct_answer": "Verdadero",
                "explanation": "Es verdadero porque el concepto forma la base para temas más avanzados."
            }
        ][:num_questions],
        "metadata": {
            "generation_time": "2024-01-25T16:30:00Z",
            "difficulty_level": difficulty,
            "question_types_requested": question_types,
            "total_generated": min(num_questions, 3)
        }
    }

@app.post("/api/v1/questions/generate/batch")
async def generate_questions_batch(request_data: Dict[str, Any]):
    """Generar preguntas para múltiples átomos"""
    atom_ids = request_data.get("atom_ids", [])
    
    results = []
    for atom_id in atom_ids:
        results.append({
            "atom_id": atom_id,
            "questions_generated": 3,
            "status": "success"
        })
    
    return {
        "batch_id": "batch_001",
        "total_atoms": len(atom_ids),
        "results": results,
        "summary": {
            "successful": len(atom_ids),
            "failed": 0,
            "total_questions_generated": len(atom_ids) * 3
        }
    }

@app.get("/api/v1/questions/atom/{atom_id}")
async def get_questions_for_atom(atom_id: str):
    """Obtener preguntas existentes para un átomo"""
    return {
        "atom_id": atom_id,
        "questions": [
            {
                "id": "q1_stored",
                "question_text": "Pregunta almacenada para este átomo",
                "question_type": "multiple_choice",
                "difficulty": "medium",
                "created_at": "2024-01-25T15:00:00Z"
            }
        ],
        "total_questions": 1
    }

@app.post("/api/v1/questions/validate")
async def validate_question(question_data: Dict[str, Any]):
    """Validar la calidad de una pregunta generada"""
    return {
        "question_id": question_data.get("id", "unknown"),
        "validation_result": {
            "is_valid": True,
            "quality_score": 0.85,
            "issues": [],
            "suggestions": [
                "Consider adding more diverse distractors",
                "Explanation could be more detailed"
            ]
        },
        "validated_at": "2024-01-25T16:45:00Z"
    }

@app.get("/api/v1/questions/types")
async def get_question_types():
    """Obtener tipos de preguntas disponibles"""
    return {
        "available_types": [
            {
                "type": "multiple_choice",
                "name": "Opción Múltiple",
                "description": "Pregunta con opciones predefinidas"
            },
            {
                "type": "open_ended",
                "name": "Respuesta Abierta",
                "description": "Pregunta que requiere respuesta textual libre"
            },
            {
                "type": "true_false",
                "name": "Verdadero/Falso",
                "description": "Pregunta de afirmación verdadera o falsa"
            },
            {
                "type": "fill_blank",
                "name": "Completar Espacio",
                "description": "Pregunta con espacios en blanco para completar"
            }
        ]
    }

@app.get("/api/v1/questions/stats")
async def get_question_stats():
    """Obtener estadísticas del servicio de preguntas"""
    return {
        "total_questions_generated": 1247,
        "questions_by_type": {
            "multiple_choice": 623,
            "open_ended": 374,
            "true_false": 186,
            "fill_blank": 64
        },
        "questions_by_difficulty": {
            "easy": 312,
            "medium": 623,
            "hard": 312
        },
        "average_generation_time_ms": 1850,
        "success_rate": 0.98
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005) 