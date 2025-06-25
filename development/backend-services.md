# Guía de Desarrollo Backend Agéntico - Atomia

## Stack Tecnológico Backend Agéntico

### Tecnologías Principales
- **Framework**: FastAPI (Python 3.11+)
- **Agentes**: LangChain + LangGraph para razonamiento educativo
- **LLM**: DeepSeek R1 vía Azure AI
- **Memoria Agéntica**: Redis (largo plazo) + ChromaDB (semántica) + Buffer (corto plazo)
- **ORM**: SQLAlchemy 2.0 con Alembic
- **Validación**: Pydantic v2
- **Async**: asyncio + httpx
- **Testing**: pytest + pytest-asyncio
- **Documentación**: OpenAPI/Swagger automático

### Arquitectura Agéntica Implementada ✅
- **Agente Educativo Principal**: ReAct con workflow Plan-Execute-Observe-Reflect
- **Sistema de Memoria Multi-Nivel**: Corto plazo, largo plazo (Redis), semántica (ChromaDB)
- **Herramientas Educativas**: 4 herramientas especializadas (search_atoms, track_progress, generate_questions, evaluate_answers)
- **Orquestador Agéntico**: Coordina el ciclo completo de razonamiento educativo

## Arquitectura de Microservicios

### Estructura de un Servicio
```
backend/services/{service_name}/
├── src/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── endpoints/
│   │   │   └── dependencies.py
│   │   └── router.py
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   └── logging.py
│   ├── domain/
│   │   ├── entities/
│   │   ├── repositories/
│   │   └── services/
│   ├── infrastructure/
│   │   ├── database/
│   │   ├── llm/
│   │   └── cache/
│   └── main.py
├── tests/
├── Dockerfile
├── requirements.txt
└── README.md
```

## Servicio de Atomización Agéntico

### API Endpoints con Integración Agéntica
```python
# services/atomization/src/api/v1/endpoints/atomization.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from typing import List
from ....domain.services import AgenticAtomizationService
from ....domain.entities import LearningAtom, AtomizationRequest
from ....core.dependencies import get_agentic_atomization_service

router = APIRouter(prefix="/atomization", tags=["atomization"])

@router.post("/atomize", response_model=List[LearningAtom])
async def atomize_content_agentic(
    request: AtomizationRequest,
    service: AgenticAtomizationService = Depends(get_agentic_atomization_service)
) -> List[LearningAtom]:
    """
    Atomiza contenido educativo usando el agente de IA con capacidades de razonamiento.
    
    - **content**: Texto del material educativo
    - **course_objectives**: Objetivos del curso (opcional)  
    - **difficulty_level**: Nivel de dificultad target
    - **user_id**: ID del usuario para contexto personalizado
    
    El agente usa el workflow Plan-Execute-Observe-Reflect para:
    1. Planificar la estrategia de atomización
    2. Ejecutar herramientas educativas especializadas
    3. Observar y validar los resultados
    4. Reflexionar sobre la calidad pedagógica
    """
    try:
        atoms = await service.atomize_with_agent(
            content=request.content,
            objectives=request.course_objectives,
            difficulty=request.difficulty_level,
            user_id=request.user_id
        )
        return atoms
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/atomize-file", response_model=List[LearningAtom])
async def atomize_file(
    file: UploadFile = File(...),
    course_objectives: str = "",
    difficulty_level: str = "intermedio",
    service: AtomizationService = Depends(get_atomization_service)
) -> List[LearningAtom]:
    """Atomiza contenido desde un archivo (PDF, TXT, DOCX)"""
    content = await extract_content_from_file(file)
    return await service.atomize(content, course_objectives, difficulty_level)

@router.put("/atoms/{atom_id}", response_model=LearningAtom)
async def update_atom(
    atom_id: str,
    atom_update: LearningAtomUpdate,
    service: AtomizationService = Depends(get_atomization_service)
) -> LearningAtom:
    """Actualiza un átomo de aprendizaje existente"""
    atom = await service.update_atom(atom_id, atom_update)
    if not atom:
        raise HTTPException(status_code=404, detail="Atom not found")
    return atom
```

### Domain Service Agéntico
```python
# services/atomization/src/domain/services/agentic_atomization_service.py
from typing import List, Optional, Dict, Any
from ..entities import LearningAtom
from ..repositories import AtomRepository
from ...infrastructure.agentic import AgenticOrchestrator, TaskType
from ...infrastructure.cache import CacheService
import structlog

logger = structlog.get_logger()

class AgenticAtomizationService:
    """Servicio de atomización que usa el agente educativo con razonamiento avanzado."""
    
    def __init__(
        self,
        atom_repository: AtomRepository,
        agentic_orchestrator: AgenticOrchestrator,
        cache_service: CacheService,
    ):
        self.atom_repository = atom_repository
        self.agent = agentic_orchestrator
        self.cache_service = cache_service
    
    async def atomize_with_agent(
        self, 
        content: str, 
        objectives: str = "",
        difficulty: str = "intermedio",
        user_id: Optional[str] = None
    ) -> List[LearningAtom]:
        """
        Atomiza contenido usando el sistema agéntico completo.
        
        El agente ejecuta el workflow Plan-Execute-Observe-Reflect:
        1. PLAN: Analiza el contenido y planifica estrategia de atomización
        2. EXECUTE: Usa herramientas educativas para crear átomos
        3. OBSERVE: Valida la calidad pedagógica de los átomos
        4. REFLECT: Mejora los átomos basado en principios educativos
        """
        logger.info("Starting agentic atomization", 
                   content_length=len(content), 
                   difficulty=difficulty,
                   user_id=user_id)
        
        # Verificar cache con contexto agéntico
        cache_key = self._generate_agentic_cache_key(content, objectives, difficulty, user_id)
        cached_result = await self.cache_service.get(cache_key)
        
        if cached_result:
            logger.info("Cache hit for atomization", cache_key=cache_key)
            return cached_result
        
        # Construir tarea educativa para el agente
        educational_task = {
            "query": f"""
            Atomiza el siguiente contenido educativo en unidades de aprendizaje coherentes:
            
            CONTENIDO: {content}
            OBJETIVOS: {objectives}
            NIVEL: {difficulty}
            
            Aplica principios pedagógicos:
            - Microaprendizaje (Skinner): Divide en unidades pequeñas y autosuficientes
            - Prerrequisitos claros: Establece dependencias entre conceptos
            - Evaluabilidad: Cada átomo debe ser fácilmente evaluable
            - Coherencia conceptual: Mantén unidad temática en cada átomo
            """,
            "user_id": user_id,
            "task_type": "ATOMIZATION",
            "context": {
                "content_type": "educational_material",
                "objectives": objectives,
                "difficulty": difficulty,
                "content_length": len(content)
            }
        }
        
        # Procesar con agente usando workflow completo
        agent_result = await self.agent.process_educational_task(educational_task)
        
        # Extraer átomos de la respuesta agéntica
        atoms_data = self._extract_atoms_from_agent_response(agent_result)
        
        # Validar y enriquecer con metadatos agénticos
        validated_atoms = await self._validate_and_enrich_atoms_agentic(
            atoms_data, 
            agent_result
        )
        
        # Guardar en base de datos con trazabilidad agéntica
        saved_atoms = await self.atom_repository.save_many_with_agent_metadata(
            validated_atoms,
            agent_metadata={
                "reasoning_steps": agent_result.get("reasoning_steps", []),
                "tools_used": agent_result.get("tools_used", []),
                "iterations": agent_result.get("iterations", 0)
            }
        )
        
        # Cachear resultado con contexto agéntico
        await self.cache_service.set(cache_key, saved_atoms, ttl=3600)
        
        logger.info("Agentic atomization completed", 
                   atoms_created=len(saved_atoms),
                   reasoning_steps=len(agent_result.get("reasoning_steps", [])))
        
        return saved_atoms
    
    def _generate_agentic_cache_key(self, content: str, objectives: str, 
                                   difficulty: str, user_id: Optional[str]) -> str:
        """Genera clave de cache considerando contexto agéntico"""
        import hashlib
        key_data = f"{content}:{objectives}:{difficulty}:{user_id or 'anonymous'}"
        return f"agentic_atoms:{hashlib.md5(key_data.encode()).hexdigest()}"
    
    def _extract_atoms_from_agent_response(self, agent_result: Dict[str, Any]) -> List[Dict]:
        """Extrae átomos de la respuesta estructurada del agente"""
        try:
            # El agente puede devolver átomos en diferentes formatos
            answer = agent_result.get("answer", "")
            
            # Intentar parsear JSON si está presente
            import json
            import re
            
            # Buscar bloques JSON en la respuesta
            json_pattern = r'```json\s*(.*?)\s*```'
            json_matches = re.findall(json_pattern, answer, re.DOTALL)
            
            for match in json_matches:
                try:
                    data = json.loads(match)
                    if isinstance(data, list) and data:
                        return data
                    elif isinstance(data, dict) and "atoms" in data:
                        return data["atoms"]
                except json.JSONDecodeError:
                    continue
            
            # Si no hay JSON, usar heurísticas para extraer átomos del texto
            return self._parse_atoms_from_text(answer)
            
        except Exception as e:
            logger.error("Error extracting atoms from agent response", error=str(e))
            return []
    
    async def _validate_and_enrich_atoms_agentic(
        self, 
        atoms_data: List[Dict],
        agent_result: Dict[str, Any]
    ) -> List[LearningAtom]:
        """Valida y enriquece átomos con metadatos agénticos adicionales"""
        from datetime import datetime
        validated = []
        
        for i, atom_data in enumerate(atoms_data):
            # Validar estructura básica
            if not self._is_valid_atom_structure(atom_data):
                logger.warning(f"Invalid atom structure at index {i}", atom_data=atom_data)
                continue
            
            # Enriquecer con metadatos agénticos
            atom_data.update({
                'created_at': datetime.utcnow(),
                'version': 1,
                'status': 'active',
                'created_by_agent': True,
                'agent_reasoning_quality': self._assess_reasoning_quality(agent_result),
                'tools_used_count': len(agent_result.get("tools_used", [])),
                'iteration_count': agent_result.get("iterations", 0)
            })
            
            # Crear entidad
            try:
                atom = LearningAtom(**atom_data)
                
                # Validar prerrequisitos existen
                if atom.prerequisites:
                    valid_prereqs = await self._validate_prerequisites(atom.prerequisites)
                    atom.prerequisites = valid_prereqs
                
                validated.append(atom)
                
            except Exception as e:
                logger.error(f"Error creating atom entity at index {i}", 
                           error=str(e), atom_data=atom_data)
                continue
        
        logger.info(f"Validated {len(validated)} atoms from {len(atoms_data)} candidates")
        return validated
    
    def _assess_reasoning_quality(self, agent_result: Dict[str, Any]) -> float:
        """Evalúa la calidad del razonamiento del agente (0.0 a 1.0)"""
        reasoning_steps = agent_result.get("reasoning_steps", [])
        tools_used = agent_result.get("tools_used", [])
        iterations = agent_result.get("iterations", 0)
        
        # Heurística simple para evaluar calidad
        quality_score = 0.5  # Base
        
        # Más pasos de razonamiento = mejor calidad
        if len(reasoning_steps) >= 3:
            quality_score += 0.2
        
        # Uso de herramientas educativas = mejor calidad
        if len(tools_used) >= 2:
            quality_score += 0.2
        
        # Iteraciones controladas = mejor calidad
        if 1 <= iterations <= 5:
            quality_score += 0.1
        
        return min(1.0, quality_score)
    
    def _parse_atoms_from_text(self, text: str) -> List[Dict]:
        """Parsea átomos de respuesta en texto libre"""
        # Implementación simplificada - en producción usar regex más sofisticado
        atoms = []
        
        # Buscar patrones tipo "Átomo 1:", "1.", etc.
        import re
        atom_pattern = r'(?:Átomo|Atom)\s*(\d+)[:\.]?\s*(.*?)(?=(?:Átomo|Atom)\s*\d+|$)'
        matches = re.findall(atom_pattern, text, re.DOTALL | re.IGNORECASE)
        
        for match in matches:
            atom_num, content = match
            if content.strip():
                atoms.append({
                    "id": f"atom_{atom_num}",
                    "title": f"Átomo de Aprendizaje {atom_num}",
                    "content": content.strip(),
                    "difficulty": "intermedio",
                    "prerequisites": [],
                    "learning_objectives": []
                })
        
        return atoms
```

## Servicio de Evaluación

### Motor de Evaluación
```python
# services/evaluation/src/domain/services/evaluation_engine.py
from typing import Dict, Any, Optional
from ..entities import Answer, Evaluation, Question
from ...infrastructure.llm import LLMOrchestrator, TaskType

class EvaluationEngine:
    def __init__(
        self,
        llm_orchestrator: LLMOrchestrator,
        student_repository: StudentRepository,
        evaluation_repository: EvaluationRepository,
    ):
        self.llm_orchestrator = llm_orchestrator
        self.student_repository = student_repository
        self.evaluation_repository = evaluation_repository
    
    async def evaluate_answer(
        self,
        answer: Answer,
        question: Question,
        student_id: str
    ) -> Evaluation:
        # Obtener contexto del estudiante
        student = await self.student_repository.get(student_id)
        student_context = self._build_student_context(student)
        
        # Evaluación según tipo de pregunta
        if question.type in ["true_false", "multiple_choice"]:
            evaluation = self._evaluate_closed_answer(answer, question)
        else:
            evaluation = await self._evaluate_open_answer(
                answer, question, student_context
            )
        
        # Actualizar modelo del estudiante
        await self._update_student_model(student, evaluation)
        
        # Guardar evaluación
        await self.evaluation_repository.save(evaluation)
        
        return evaluation
    
    def _evaluate_closed_answer(
        self, 
        answer: Answer, 
        question: Question
    ) -> Evaluation:
        """Evalúa respuestas cerradas con lógica simple"""
        is_correct = answer.value == question.correct_answer
        score = 1.0 if is_correct else 0.0
        
        return Evaluation(
            answer_id=answer.id,
            question_id=question.id,
            score=score,
            is_correct=is_correct,
            feedback=self._get_basic_feedback(is_correct, question),
            misconceptions=[],
            knowledge_gaps=[]
        )
    
    async def _evaluate_open_answer(
        self,
        answer: Answer,
        question: Question,
        student_context: Dict[str, Any]
    ) -> Evaluation:
        """Evalúa respuestas abiertas usando LLM"""
        prompt = self._build_evaluation_prompt(
            answer=answer.value,
            question=question,
            correct_answer=question.correct_answer_model,
            student_context=student_context
        )
        
        response = await self.llm_orchestrator.process(
            task_type=TaskType.ANSWER_EVALUATION,
            prompt=prompt
        )
        
        evaluation_data = self._parse_evaluation_response(response)
        
        return Evaluation(
            answer_id=answer.id,
            question_id=question.id,
            **evaluation_data
        )
    
    async def _update_student_model(
        self, 
        student: Student, 
        evaluation: Evaluation
    ):
        """Actualiza el modelo de conocimiento del estudiante"""
        # Actualizar dominio del concepto
        concept_id = evaluation.question.atom_id
        current_mastery = student.knowledge_state.get(concept_id, 0.5)
        
        # Algoritmo simple de actualización (puede ser SAKT)
        learning_rate = 0.1
        if evaluation.is_correct:
            new_mastery = current_mastery + learning_rate * (1 - current_mastery)
        else:
            new_mastery = current_mastery - learning_rate * current_mastery
        
        student.knowledge_state[concept_id] = new_mastery
        
        # Actualizar estadísticas
        student.total_answers += 1
        if evaluation.is_correct:
            student.correct_answers += 1
        
        await self.student_repository.update(student)
```

## Servicio de Planificación Adaptativa

### Planificador con FSRS
```python
# services/planning/src/domain/services/adaptive_planner.py
from typing import List, Optional
from datetime import datetime, timedelta
from ..entities import StudyPlan, StudySession, LearningAtom
from ...infrastructure.algorithms import FSRSAlgorithm

class AdaptivePlanner:
    def __init__(
        self,
        student_repository: StudentRepository,
        atom_repository: AtomRepository,
        llm_orchestrator: LLMOrchestrator,
        fsrs_algorithm: FSRSAlgorithm,
    ):
        self.student_repository = student_repository
        self.atom_repository = atom_repository
        self.llm_orchestrator = llm_orchestrator
        self.fsrs = fsrs_algorithm
    
    async def get_next_atoms(
        self,
        student_id: str,
        session_duration: int = 30  # minutos
    ) -> List[LearningAtom]:
        # Obtener estado del estudiante
        student = await self.student_repository.get(student_id)
        
        # Obtener átomos pendientes de repaso (FSRS)
        review_atoms = await self._get_review_atoms(student)
        
        # Obtener nuevos átomos según progreso
        new_atoms = await self._get_new_atoms(student)
        
        # Balancear repaso vs nuevo contenido
        session_atoms = await self._balance_session(
            review_atoms,
            new_atoms,
            student,
            session_duration
        )
        
        # Optimizar secuencia con LLM
        optimized_sequence = await self._optimize_sequence(
            session_atoms,
            student
        )
        
        return optimized_sequence
    
    async def _get_review_atoms(self, student: Student) -> List[LearningAtom]:
        """Obtiene átomos que necesitan repaso según FSRS"""
        review_items = []
        
        for atom_id, card_state in student.spaced_repetition_state.items():
            if self.fsrs.is_due_for_review(card_state):
                atom = await self.atom_repository.get(atom_id)
                if atom:
                    review_items.append((atom, card_state))
        
        # Ordenar por urgencia
        review_items.sort(
            key=lambda x: self.fsrs.calculate_urgency(x[1]),
            reverse=True
        )
        
        return [item[0] for item in review_items[:10]]  # Max 10 repasos
    
    async def _get_new_atoms(self, student: Student) -> List[LearningAtom]:
        """Obtiene nuevos átomos basados en prerrequisitos cumplidos"""
        # Obtener todos los átomos
        all_atoms = await self.atom_repository.get_all()
        
        # Filtrar por prerrequisitos cumplidos
        eligible_atoms = []
        for atom in all_atoms:
            if atom.id in student.completed_atoms:
                continue
            
            # Verificar prerrequisitos
            prereqs_met = all(
                prereq in student.completed_atoms 
                for prereq in atom.prerequisites
            )
            
            if prereqs_met:
                # Calcular score de idoneidad
                suitability_score = self._calculate_suitability(atom, student)
                eligible_atoms.append((atom, suitability_score))
        
        # Ordenar por idoneidad
        eligible_atoms.sort(key=lambda x: x[1], reverse=True)
        
        return [item[0] for item in eligible_atoms[:5]]  # Max 5 nuevos
    
    async def _balance_session(
        self,
        review_atoms: List[LearningAtom],
        new_atoms: List[LearningAtom],
        student: Student,
        duration: int
    ) -> List[LearningAtom]:
        """Balancea contenido de repaso vs nuevo"""
        # Regla simple: 60% repaso, 40% nuevo si hay repasos pendientes
        estimated_atoms = duration // 10  # ~10 min por átomo
        
        if review_atoms:
            review_count = int(estimated_atoms * 0.6)
            new_count = estimated_atoms - review_count
        else:
            review_count = 0
            new_count = estimated_atoms
        
        session_atoms = (
            review_atoms[:review_count] + 
            new_atoms[:new_count]
        )
        
        return session_atoms
    
    async def update_after_session(
        self,
        student_id: str,
        session_results: List[SessionResult]
    ):
        """Actualiza el estado después de una sesión"""
        student = await self.student_repository.get(student_id)
        
        for result in session_results:
            atom_id = result.atom_id
            
            # Actualizar FSRS
            if atom_id in student.spaced_repetition_state:
                card_state = student.spaced_repetition_state[atom_id]
                new_state = self.fsrs.update_card(
                    card_state,
                    result.score,
                    result.response_time
                )
                student.spaced_repetition_state[atom_id] = new_state
            else:
                # Primera vez viendo el átomo
                student.spaced_repetition_state[atom_id] = (
                    self.fsrs.create_new_card()
                )
            
            # Marcar como completado si score alto
            if result.score >= 0.8:
                student.completed_atoms.add(atom_id)
        
        await self.student_repository.update(student)
```

## Servicio de Gamificación

### Sistema de Logros y Recompensas
```python
# services/gamification/src/domain/services/achievement_service.py
from typing import List, Optional
from ..entities import Achievement, UserProgress, Reward
from ...infrastructure.rules import AchievementRules

class AchievementService:
    def __init__(
        self,
        achievement_repository: AchievementRepository,
        progress_repository: ProgressRepository,
        notification_service: NotificationService,
        rules_engine: AchievementRules
    ):
        self.achievement_repository = achievement_repository
        self.progress_repository = progress_repository
        self.notification_service = notification_service
        self.rules_engine = rules_engine
    
    async def check_achievements(
        self,
        user_id: str,
        event_type: str,
        event_data: Dict[str, Any]
    ) -> List[Achievement]:
        """Verifica si el usuario ha desbloqueado nuevos logros"""
        # Obtener progreso actual
        progress = await self.progress_repository.get(user_id)
        
        # Obtener logros no desbloqueados
        all_achievements = await self.achievement_repository.get_all()
        unlocked_ids = set(progress.unlocked_achievements)
        
        new_achievements = []
        
        for achievement in all_achievements:
            if achievement.id in unlocked_ids:
                continue
            
            # Verificar si cumple criterios
            if self.rules_engine.check_criteria(
                achievement,
                progress,
                event_type,
                event_data
            ):
                # Desbloquear logro
                await self._unlock_achievement(user_id, achievement)
                new_achievements.append(achievement)
        
        return new_achievements
    
    async def _unlock_achievement(
        self,
        user_id: str,
        achievement: Achievement
    ):
        """Desbloquea un logro y otorga recompensas"""
        # Actualizar progreso
        progress = await self.progress_repository.get(user_id)
        progress.unlocked_achievements.append(achievement.id)
        progress.total_points += achievement.points
        
        # Otorgar recompensas adicionales
        if achievement.rewards:
            for reward in achievement.rewards:
                await self._grant_reward(user_id, reward)
        
        await self.progress_repository.update(progress)
        
        # Notificar al usuario
        await self.notification_service.send(
            user_id=user_id,
            type="achievement_unlocked",
            data={
                "achievement": achievement.to_dict(),
                "message": f"¡Has desbloqueado '{achievement.title}'!"
            }
        )
    
    async def calculate_streaks(self, user_id: str) -> Dict[str, int]:
        """Calcula rachas de estudio"""
        sessions = await self.progress_repository.get_study_sessions(
            user_id,
            days=30
        )
        
        # Racha diaria
        daily_streak = self._calculate_daily_streak(sessions)
        
        # Racha semanal
        weekly_streak = self._calculate_weekly_streak(sessions)
        
        # Actualizar si hay nuevos records
        progress = await self.progress_repository.get(user_id)
        if daily_streak > progress.max_daily_streak:
            progress.max_daily_streak = daily_streak
            await self._check_streak_achievements(user_id, "daily", daily_streak)
        
        return {
            "daily": daily_streak,
            "weekly": weekly_streak,
            "max_daily": progress.max_daily_streak
        }
```

## API Gateway Agéntico

### Configuración Principal con Capacidades Agénticas
```python
# backend/api_gateway/src/main.py
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
import httpx
import structlog

from .core.config import settings
from .core.middleware import (
    RateLimitMiddleware,
    AuthenticationMiddleware,
    RequestIdMiddleware,
    AgenticContextMiddleware  # Nuevo middleware para contexto agéntico
)
from .api.routers import (
    auth_router,
    learning_router,
    progress_router,
    admin_router,
    agentic_router  # Nuevo router para endpoints agénticos
)

logger = structlog.get_logger()

app = FastAPI(
    title="Atomia API Gateway Agéntico",
    description="Gateway principal para el Agente de IA Educativo con capacidades agénticas avanzadas",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Middleware con capacidades agénticas
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS)
app.add_middleware(RequestIdMiddleware)
app.add_middleware(AgenticContextMiddleware)  # Captura contexto para agentes
app.add_middleware(AuthenticationMiddleware, public_paths=["/api/auth/login", "/api/health", "/api/agent/health"])
app.add_middleware(RateLimitMiddleware, requests_per_minute=60)

# Instrumentación Prometheus con métricas agénticas
instrumentator = Instrumentator()
instrumentator.instrument(app).expose(app)

# Métricas agénticas personalizadas
from prometheus_client import Counter, Histogram, Gauge

agentic_requests_total = Counter(
    'agentic_requests_total',
    'Total requests processed by agentic system',
    ['endpoint', 'task_type', 'status']
)

agentic_reasoning_duration = Histogram(
    'agentic_reasoning_duration_seconds',
    'Time spent in agent reasoning',
    ['task_type', 'iterations']
)

active_agent_sessions = Gauge(
    'active_agent_sessions',
    'Number of active agent sessions'
)

# Routers tradicionales
app.include_router(auth_router, prefix="/api/auth", tags=["authentication"])
app.include_router(learning_router, prefix="/api/learning", tags=["learning"])
app.include_router(progress_router, prefix="/api/progress", tags=["progress"])
app.include_router(admin_router, prefix="/api/admin", tags=["admin"])

# Router agéntico
app.include_router(agentic_router, prefix="/api/agent", tags=["agentic"])

# Proxy a microservicios con capacidades agénticas
service_clients = {
    "atomization": httpx.AsyncClient(base_url=settings.ATOMIZATION_SERVICE_URL),
    "evaluation": httpx.AsyncClient(base_url=settings.EVALUATION_SERVICE_URL),
    "planning": httpx.AsyncClient(base_url=settings.PLANNING_SERVICE_URL),
    "gamification": httpx.AsyncClient(base_url=settings.GAMIFICATION_SERVICE_URL),
    "llm_orchestrator": httpx.AsyncClient(base_url=settings.LLM_ORCHESTRATOR_URL),  # Sistema agéntico principal
}

# Router Agéntico
@app.post("/api/agent/process")
async def process_educational_task_via_gateway(request: dict):
    """
    Procesa una tarea educativa a través del sistema agéntico.
    
    Delega al servicio llm_orchestrator que maneja:
    - Workflow Plan-Execute-Observe-Reflect
    - Memoria multi-nivel
    - Herramientas educativas especializadas
    """
    try:
        with agentic_reasoning_duration.time():
            response = await service_clients["llm_orchestrator"].post(
                "/agent/process",
                json=request,
                timeout=30.0
            )
            
        if response.status_code == 200:
            result = response.json()
            agentic_requests_total.labels(
                endpoint="process",
                task_type=request.get("task_type", "unknown"),
                status="success"
            ).inc()
            return result
        else:
            logger.error("Agentic service error", status=response.status_code, text=response.text)
            agentic_requests_total.labels(
                endpoint="process",
                task_type=request.get("task_type", "unknown"),
                status="error"
            ).inc()
            raise HTTPException(status_code=response.status_code, detail=response.text)
            
    except Exception as e:
        logger.error("Gateway agentic error", error=str(e))
        agentic_requests_total.labels(
            endpoint="process",
            task_type=request.get("task_type", "unknown"),
            status="error"
        ).inc()
        raise HTTPException(status_code=500, detail=f"Agentic processing error: {str(e)}")

@app.get("/api/agent/memory/search")
async def search_agent_memory(query: str, user_id: str = None, limit: int = 5):
    """Busca en la memoria semántica del agente"""
    try:
        response = await service_clients["llm_orchestrator"].post(
            "/agent/memory/search",
            params={"query": query, "user_id": user_id, "limit": limit}
        )
        return response.json()
    except Exception as e:
        logger.error("Memory search error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/agent/context/{user_id}")
async def get_user_agentic_context(user_id: str):
    """Obtiene el contexto completo de un usuario del sistema agéntico"""
    try:
        response = await service_clients["llm_orchestrator"].get(f"/agent/context/{user_id}")
        return response.json()
    except Exception as e:
        logger.error("Context retrieval error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    """Health check endpoint with agentic system status"""
    services_health = {}
    agentic_capabilities = {}
    
    for service_name, client in service_clients.items():
        try:
            response = await client.get("/health", timeout=2.0)
            services_health[service_name] = response.status_code == 200
            
            # Check agentic capabilities for llm_orchestrator
            if service_name == "llm_orchestrator" and services_health[service_name]:
                try:
                    agent_health = await client.get("/agent/health")
                    if agent_health.status_code == 200:
                        agent_status = agent_health.json()
                        agentic_capabilities = {
                            "agent_active": agent_status.get("agent_active", False),
                            "memory_systems": agent_status.get("memory_systems", {}),
                            "tools_available": agent_status.get("tools_count", 0),
                            "reasoning_enabled": agent_status.get("reasoning_enabled", False)
                        }
                except:
                    agentic_capabilities = {"status": "degraded"}
                    
        except:
            services_health[service_name] = False
    
    all_healthy = all(services_health.values())
    agentic_healthy = agentic_capabilities.get("agent_active", False)
    
    return {
        "status": "healthy" if all_healthy else "degraded",
        "services": services_health,
        "agentic_system": {
            "status": "healthy" if agentic_healthy else "degraded",
            "capabilities": agentic_capabilities
        },
        "features": {
            "traditional_services": all_healthy,
            "agentic_reasoning": agentic_healthy,
            "memory_systems": agentic_capabilities.get("memory_systems", {}).get("all_active", False)
        }
    }

@app.on_event("shutdown")
async def shutdown_event():
    """Cerrar conexiones al apagar"""
    for client in service_clients.values():
        await client.aclose()
```

## Testing Strategy Agéntico

### Unit Tests con Capacidades Agénticas
```python
# tests/unit/test_agentic_atomization_service.py
import pytest
from unittest.mock import Mock, AsyncMock, patch
from services.atomization.domain.services import AgenticAtomizationService

@pytest.fixture
def mock_agentic_dependencies():
    return {
        "atom_repository": Mock(),
        "agentic_orchestrator": Mock(),
        "cache_service": Mock()
    }

@pytest.mark.asyncio
async def test_atomize_with_agent_cache_hit(mock_agentic_dependencies):
    # Arrange
    service = AgenticAtomizationService(**mock_agentic_dependencies)
    cached_atoms = [{"id": "atom_1", "title": "Cached Agentic Atom"}]
    mock_agentic_dependencies["cache_service"].get = AsyncMock(return_value=cached_atoms)
    
    # Act
    result = await service.atomize_with_agent("test content", user_id="test_user")
    
    # Assert
    assert len(result) == 1
    assert result[0]["title"] == "Cached Agentic Atom"
    mock_agentic_dependencies["agentic_orchestrator"].process_educational_task.assert_not_called()

@pytest.mark.asyncio
async def test_atomize_with_agent_workflow(mock_agentic_dependencies):
    # Arrange
    service = AgenticAtomizationService(**mock_agentic_dependencies)
    mock_agentic_dependencies["cache_service"].get = AsyncMock(return_value=None)
    
    # Mock agent response with reasoning steps
    mock_agent_response = {
        "answer": """
        ```json
        [
            {
                "id": "atom_1",
                "title": "Función Lineal",
                "content": "Una función lineal es...",
                "difficulty": "intermedio",
                "prerequisites": [],
                "learning_objectives": ["Definir función lineal"]
            }
        ]
        ```
        """,
        "reasoning_steps": [
            "PLAN: Analizar contenido para identificar conceptos clave",
            "EXECUTE: Usar herramienta search_atoms para validar estructura",
            "OBSERVE: Verificar coherencia pedagógica de los átomos",
            "REFLECT: Los átomos cumplen principios de microaprendizaje"
        ],
        "tools_used": ["search_learning_atoms", "track_learning_progress"],
        "iterations": 3
    }
    
    mock_agentic_dependencies["agentic_orchestrator"].process_educational_task = AsyncMock(
        return_value=mock_agent_response
    )
    
    mock_agentic_dependencies["atom_repository"].save_many_with_agent_metadata = AsyncMock(
        return_value=[Mock(id="atom_1", title="Función Lineal")]
    )
    
    # Act
    result = await service.atomize_with_agent(
        content="Las funciones lineales son...",
        objectives="Enseñar álgebra básica",
        difficulty="intermedio",
        user_id="test_user"
    )
    
    # Assert
    assert len(result) == 1
    
    # Verificar que se llamó al agente con la tarea correcta
    call_args = mock_agentic_dependencies["agentic_orchestrator"].process_educational_task.call_args[0][0]
    assert "Atomiza el siguiente contenido" in call_args["query"]
    assert call_args["user_id"] == "test_user"
    assert call_args["task_type"] == "ATOMIZATION"
    
    # Verificar que se guardaron metadatos agénticos
    save_call_args = mock_agentic_dependencies["atom_repository"].save_many_with_agent_metadata.call_args
    agent_metadata = save_call_args[1]["agent_metadata"]
    assert len(agent_metadata["reasoning_steps"]) == 4
    assert len(agent_metadata["tools_used"]) == 2
    assert agent_metadata["iterations"] == 3

@pytest.mark.asyncio
async def test_agent_reasoning_quality_assessment(mock_agentic_dependencies):
    # Arrange
    service = AgenticAtomizationService(**mock_agentic_dependencies)
    
    # Mock response with high-quality reasoning
    high_quality_response = {
        "reasoning_steps": ["PLAN", "EXECUTE", "OBSERVE", "REFLECT", "REFINE"],
        "tools_used": ["search_atoms", "evaluate_answer", "generate_questions"],
        "iterations": 3
    }
    
    # Act
    quality_score = service._assess_reasoning_quality(high_quality_response)
    
    # Assert
    assert quality_score >= 0.8  # High quality reasoning
    
    # Test low quality response
    low_quality_response = {
        "reasoning_steps": ["PLAN"],
        "tools_used": [],
        "iterations": 0
    }
    
    quality_score_low = service._assess_reasoning_quality(low_quality_response)
    assert quality_score_low <= 0.6  # Lower quality
```

### Integration Tests Agénticos
```python
# tests/integration/test_agentic_api.py
import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient

@pytest.mark.asyncio
async def test_complete_agentic_study_flow(async_client: AsyncClient, auth_headers):
    """Test completo del flujo de estudio usando capacidades agénticas"""
    
    # 1. Atomizar contenido con agente
    atomization_request = {
        "query": "Atomiza este contenido de matemáticas: Las funciones lineales son relaciones...",
        "user_id": "test_user_123",
        "task_type": "ATOMIZATION",
        "context": {
            "objectives": "Enseñar álgebra básica",
            "difficulty": "intermedio"
        }
    }
    
    response = await async_client.post(
        "/api/agent/process",
        json=atomization_request,
        headers=auth_headers
    )
    assert response.status_code == 200
    atomization_result = response.json()
    
    # Verificar respuesta agéntica
    assert "answer" in atomization_result
    assert "reasoning_steps" in atomization_result
    assert "tools_used" in atomization_result
    assert atomization_result["iterations"] > 0
    
    # 2. Generar preguntas con agente
    question_request = {
        "query": "Genera 3 preguntas sobre funciones lineales para nivel intermedio",
        "user_id": "test_user_123",
        "task_type": "QUESTION_GENERATION",
        "context": {
            "atom_id": "function_linear_001",
            "difficulty": "intermedio",
            "question_types": ["conceptual", "application"]
        }
    }
    
    response = await async_client.post(
        "/api/agent/process",
        json=question_request,
        headers=auth_headers
    )
    assert response.status_code == 200
    questions_result = response.json()
    
    # Verificar generación de preguntas
    assert "search_learning_atoms" in questions_result["tools_used"]
    assert len(questions_result["reasoning_steps"]) >= 3
    
    # 3. Evaluar respuesta con agente
    evaluation_request = {
        "query": "Evalúa esta respuesta: 'Una función lineal tiene la forma y = mx + b'",
        "user_id": "test_user_123", 
        "task_type": "ANSWER_EVALUATION",
        "context": {
            "question": "¿Cuál es la forma general de una función lineal?",
            "correct_answer": "y = mx + b donde m es la pendiente y b es la ordenada al origen"
        }
    }
    
    response = await async_client.post(
        "/api/agent/process",
        json=evaluation_request,
        headers=auth_headers
    )
    assert response.status_code == 200
    evaluation_result = response.json()
    
    # Verificar evaluación agéntica
    assert "evaluate_user_answer" in evaluation_result["tools_used"]
    assert "track_learning_progress" in evaluation_result["tools_used"]
    
    # 4. Verificar memoria agéntica actualizada
    response = await async_client.get(
        "/api/agent/context/test_user_123",
        headers=auth_headers
    )
    assert response.status_code == 200
    context = response.json()
    
    # Verificar que el contexto incluye las interacciones
    assert "chat_history" in context
    assert len(context["chat_history"]) > 0
    
    # 5. Buscar en memoria semántica
    response = await async_client.get(
        "/api/agent/memory/search",
        params={
            "query": "funciones lineales",
            "user_id": "test_user_123",
            "limit": 5
        },
        headers=auth_headers
    )
    assert response.status_code == 200
    memory_results = response.json()
    
    # Verificar búsqueda semántica
    assert "results" in memory_results
    assert len(memory_results["results"]) > 0

@pytest.mark.asyncio
async def test_agentic_workflow_integration(async_client: AsyncClient, auth_headers):
    """Test del workflow Plan-Execute-Observe-Reflect completo"""
    
    complex_request = {
        "query": """
        Ayuda a un estudiante de nivel intermedio que está confundido sobre 
        la diferencia entre funciones lineales y cuadráticas. Atomiza el contenido,
        genera preguntas adaptativas, y evalúa su comprensión.
        """,
        "user_id": "confused_student_456",
        "task_type": "COMPREHENSIVE_LEARNING",
        "context": {
            "learning_style": "visual",
            "previous_errors": ["confunde pendiente con término independiente"],
            "strengths": ["bueno con gráficos"]
        }
    }
    
    response = await async_client.post(
        "/api/agent/process",
        json=complex_request,
        headers=auth_headers,
        timeout=60.0  # Timeout mayor para tareas complejas
    )
    
    assert response.status_code == 200
    result = response.json()
    
    # Verificar workflow completo
    reasoning_steps = result["reasoning_steps"]
    assert any("PLAN" in step for step in reasoning_steps)
    assert any("EXECUTE" in step for step in reasoning_steps)
    assert any("OBSERVE" in step for step in reasoning_steps)
    assert any("REFLECT" in step for step in reasoning_steps)
    
    # Verificar uso de múltiples herramientas
    tools_used = result["tools_used"]
    expected_tools = [
        "search_learning_atoms",
        "generate_adaptive_questions", 
        "evaluate_user_answer",
        "track_learning_progress"
    ]
    
    for tool in expected_tools:
        assert tool in tools_used, f"Tool {tool} should have been used"
    
    # Verificar iteraciones de razonamiento
    assert result["iterations"] >= 2, "Complex tasks should require multiple iterations"
    assert result["iterations"] <= 10, "Should not exceed maximum iterations"

@pytest.mark.asyncio
async def test_agentic_error_handling(async_client: AsyncClient, auth_headers):
    """Test manejo de errores en el sistema agéntico"""
    
    # Request malformado
    bad_request = {
        "query": "",  # Query vacío
        "user_id": None,
        "task_type": "INVALID_TYPE"
    }
    
    response = await async_client.post(
        "/api/agent/process",
        json=bad_request,
        headers=auth_headers
    )
    
    # Debería manejar gracefully el error
    assert response.status_code in [400, 422, 500]
    
    # Request que causa timeout del agente
    timeout_request = {
        "query": "Genera 10000 preguntas sobre todos los temas de matemáticas",
        "user_id": "test_user",
        "task_type": "QUESTION_GENERATION"
    }
    
    response = await async_client.post(
        "/api/agent/process", 
        json=timeout_request,
        headers=auth_headers,
        timeout=5.0  # Timeout corto para forzar error
    )
    
    # Debería manejar timeout gracefully
    assert response.status_code in [408, 500, 504]
```

## Deployment Configuration

### Docker Compose para Desarrollo
```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: atomia
      POSTGRES_PASSWORD: atomia_pass
      POSTGRES_DB: atomia_db
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
  
  mongodb:
    image: mongo:6
    environment:
      MONGO_INITDB_ROOT_USERNAME: atomia
      MONGO_INITDB_ROOT_PASSWORD: atomia_pass
    volumes:
      - mongo_data:/data/db
    ports:
      - "27017:27017"
  
  neo4j:
    image: neo4j:5
    environment:
      NEO4J_AUTH: neo4j/atomia_pass
    volumes:
      - neo4j_data:/data
    ports:
      - "7687:7687"
      - "7474:7474"
  
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
  
  rabbitmq:
    image: rabbitmq:3-management
    environment:
      RABBITMQ_DEFAULT_USER: atomia
      RABBITMQ_DEFAULT_PASS: atomia_pass
    ports:
      - "5672:5672"
      - "15672:15672"
  
  api_gateway:
    build: ./backend/api_gateway
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://atomia:atomia_pass@postgres:5432/atomia_db
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis
    volumes:
      - ./backend/api_gateway:/app
    command: uvicorn src.main:app --reload --host 0.0.0.0
  
  atomization_service:
    build: ./backend/services/atomization
    environment:
      - MONGODB_URL=mongodb://atomia:atomia_pass@mongodb:27017
      - REDIS_URL=redis://redis:6379
      - AZURE_AI_KEY=${AZURE_AI_KEY}
      - AZURE_AI_ENDPOINT=${AZURE_AI_ENDPOINT}
    depends_on:
      - mongodb
      - redis
    volumes:
      - ./backend/services/atomization:/app

volumes:
  postgres_data:
  mongo_data:
  neo4j_data:
```

### Kubernetes para Producción
```yaml
# k8s/atomization-service.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: atomization-service
  namespace: atomia
spec:
  replicas: 3
  selector:
    matchLabels:
      app: atomization-service
  template:
    metadata:
      labels:
        app: atomization-service
    spec:
      containers:
      - name: atomization
        image: atomia/atomization-service:latest
        ports:
        - containerPort: 8000
        env:
        - name: MONGODB_URL
          valueFrom:
            secretKeyRef:
              name: mongodb-secret
              key: connection-string
        - name: AZURE_AI_KEY
          valueFrom:
            secretKeyRef:
              name: azure-ai-secret
              key: api-key
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: atomization-service
  namespace: atomia
spec:
  selector:
    app: atomization-service
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP
``` 