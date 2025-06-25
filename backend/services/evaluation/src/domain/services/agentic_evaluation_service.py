"""
Servicio Agéntico de Evaluación con Workflow Plan-Execute-Observe-Reflect
"""

import json
import re
import hashlib
import structlog
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import uuid

from ...schemas import (
    EvaluationRequest, EvaluationResponse, FeedbackDetail,
    Misconception, LearningProgress, AgentMetadata,
    DifficultyLevel, EvaluationType
)

logger = structlog.get_logger()


class AgenticEvaluationService:
    """
    Servicio principal para evaluación agéntica de respuestas de estudiantes.
    Implementa el workflow Plan-Execute-Observe-Reflect para razonamiento educativo.
    """
    
    def __init__(
        self,
        evaluation_repository,  # EvaluationRepository
        agentic_orchestrator,  # AgenticOrchestratorClient  
        cache_service  # RedisCacheService
    ):
        self.evaluation_repository = evaluation_repository
        self.agentic_orchestrator = agentic_orchestrator
        self.cache_service = cache_service
    
    async def evaluate_student_response(
        self, 
        request: EvaluationRequest
    ) -> EvaluationResponse:
        """
        Evalúa la respuesta de un estudiante usando el agente educativo.
        Implementa el ciclo completo Plan-Execute-Observe-Reflect.
        """
        start_time = datetime.utcnow()
        
        # Verificar cache agéntico
        cache_key = self._generate_cache_key(request)
        cached_result = await self.cache_service.get(cache_key)
        if cached_result:
            logger.info("Using cached evaluation", user_id=request.user_id)
            return EvaluationResponse(**cached_result)
        
        try:
            # Construir tarea educativa para el agente
            educational_task = self._build_evaluation_task(request)
            
            # Invocar al agente con workflow completo
            logger.info(
                "Starting agentic evaluation",
                user_id=request.user_id,
                question_id=request.question_id,
                evaluation_type=request.evaluation_type
            )
            
            agent_result = await self.agentic_orchestrator.process_educational_task(
                task_type=educational_task["task_type"],
                query=educational_task["query"],
                user_id=educational_task["user_id"],
                context=educational_task.get("context"),
                metadata=None
            )
            
            # Extraer evaluación de la respuesta del agente
            evaluation_data = self._extract_evaluation_from_agent(
                agent_result, request
            )
            
            # Enriquecer con metadatos agénticos
            evaluation_response = await self._enrich_evaluation_response(
                evaluation_data, agent_result, request, start_time
            )
            
            # Guardar evaluación en la base de datos
            await self.evaluation_repository.save_evaluation(
                evaluation=evaluation_response,
                user_id=request.user_id,
                question_id=request.question_id
            )
            
            # Actualizar el progreso del usuario en la tabla de dominio (mastery)
            if request.context and request.context.atom_id:
                await self.evaluation_repository.update_user_progress(
                    user_id=request.user_id,
                    atom_id=request.context.atom_id,
                    mastery_level=evaluation_response.learning_progress.current_mastery
                )

            # Cachear resultado
            await self.cache_service.set(
                cache_key, 
                evaluation_response.dict(),
                ttl=3600  # 1 hora
            )
            
            logger.info(
                "Evaluation completed",
                evaluation_id=evaluation_response.evaluation_id,
                score=evaluation_response.score,
                confidence=evaluation_response.agent_metadata.confidence_score
            )
            
            return evaluation_response
            
        except Exception as e:
            logger.error(
                "Error in agentic evaluation",
                error=str(e),
                user_id=request.user_id,
                question_id=request.question_id
            )
            
            # Generar evaluación de fallback
            return self._create_fallback_evaluation(request, str(e), start_time)
    
    def _build_evaluation_task(self, request: EvaluationRequest) -> Dict[str, Any]:
        """Construye la tarea educativa para el agente evaluador"""
        
        # Construir prompt especializado para evaluación
        evaluation_prompt = f"""
        TAREA: Evaluar la respuesta de un estudiante de manera pedagógica y constructiva.
        
        PREGUNTA:
        {request.question_text}
        
        RESPUESTA DEL ESTUDIANTE:
        {request.student_answer}
        
        CONCEPTOS ESPERADOS:
        {', '.join(request.expected_concepts) if request.expected_concepts else "No especificados"}
        
        NIVEL DE DIFICULTAD: {request.difficulty_level}
        TIPO DE EVALUACIÓN: {request.evaluation_type}
        
        INSTRUCCIONES PEDAGÓGICAS:
        1. Aplicar principios de evaluación formativa: feedback constructivo
        2. Detectar conceptos erróneos y proporcionar correcciones claras
        3. Identificar fortalezas y áreas de mejora específicas
        4. Generar sugerencias concretas de estudio
        5. Evaluar el progreso de aprendizaje del estudiante
        
        FORMATO DE RESPUESTA:
        Proporciona la evaluación en formato JSON con la siguiente estructura:
        ```json
        {{
            "score": 0.0-1.0,
            "strengths": ["punto1", "punto2"],
            "improvements": ["mejora1", "mejora2"],
            "suggestions": ["sugerencia1", "sugerencia2"],
            "misconceptions": [
                {{
                    "concept": "concepto",
                    "description": "descripción del error",
                    "severity": 0.0-1.0,
                    "correction": "corrección sugerida"
                }}
            ],
            "key_concepts_understood": ["concepto1", "concepto2"],
            "next_topics": ["tema1", "tema2"],
            "mastery_level": 0.0-1.0,
            "confidence": 0.0-1.0
        }}
        ```
        """
        
        # Añadir contexto si está disponible
        if request.context:
            evaluation_prompt += f"\n\nCONTEXTO ADICIONAL:\n{json.dumps(request.context.dict())}"
        
        return {
            "query": evaluation_prompt,
            "user_id": request.user_id,
            "task_type": "EVALUATION",
            "context": {
                "question_id": request.question_id,
                "evaluation_type": request.evaluation_type.value,
                "difficulty": request.difficulty_level.value,
                "expected_concepts": request.expected_concepts,
                "previous_attempts": request.context.previous_attempts if request.context else 0
            }
        }
    
    def _generate_cache_key(self, request: EvaluationRequest) -> str:
        """Genera clave de cache considerando contexto de evaluación"""
        key_data = f"{request.question_id}:{request.student_answer}:{request.user_id}"
        hash_key = hashlib.md5(key_data.encode()).hexdigest()
        return f"agentic_eval:{hash_key}"
    
    def _extract_evaluation_from_agent(
        self, 
        agent_result: Dict[str, Any],
        request: EvaluationRequest
    ) -> Dict[str, Any]:
        """Extrae datos de evaluación de la respuesta del agente"""
        try:
            answer = agent_result.get("answer", "")
            
            # Buscar JSON en la respuesta
            json_pattern = r'```json\s*(.*?)\s*```'
            json_matches = re.findall(json_pattern, answer, re.DOTALL)
            
            if json_matches:
                try:
                    eval_data = json.loads(json_matches[0])
                    return self._validate_evaluation_data(eval_data)
                except json.JSONDecodeError:
                    pass
            
            # Si no hay JSON válido, usar heurísticas
            return self._parse_evaluation_from_text(answer, request)
            
        except Exception as e:
            logger.error("Error extracting evaluation", error=str(e))
            return self._create_default_evaluation_data()
    
    def _validate_evaluation_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Valida y normaliza los datos de evaluación"""
        # Asegurar campos requeridos
        data.setdefault("score", 0.5)
        data.setdefault("strengths", [])
        data.setdefault("improvements", [])
        data.setdefault("suggestions", [])
        data.setdefault("misconceptions", [])
        data.setdefault("key_concepts_understood", [])
        data.setdefault("next_topics", [])
        data.setdefault("mastery_level", data.get("score", 0.5))
        data.setdefault("confidence", 0.8)
        
        # Validar rangos
        data["score"] = max(0.0, min(1.0, float(data["score"])))
        data["mastery_level"] = max(0.0, min(1.0, float(data["mastery_level"])))
        data["confidence"] = max(0.0, min(1.0, float(data["confidence"])))
        
        return data
    
    def _parse_evaluation_from_text(
        self, 
        text: str,
        request: EvaluationRequest
    ) -> Dict[str, Any]:
        """Parsea evaluación de texto libre usando heurísticas"""
        # Implementación básica de parsing
        score = 0.5  # Default
        
        # Buscar patrones de puntuación
        score_patterns = [
            r'puntuación[:\s]+(\d+(?:\.\d+)?)',
            r'score[:\s]+(\d+(?:\.\d+)?)',
            r'calificación[:\s]+(\d+(?:\.\d+)?)'
        ]
        
        for pattern in score_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    score = float(match.group(1))
                    if score > 1.0:
                        score = score / 100.0  # Convertir porcentaje
                    break
                except:
                    pass
        
        return {
            "score": score,
            "strengths": ["Respuesta proporcionada"],
            "improvements": ["Revisar conceptos clave"],
            "suggestions": ["Estudiar material adicional"],
            "misconceptions": [],
            "key_concepts_understood": [],
            "next_topics": request.expected_concepts[:2] if request.expected_concepts else [],
            "mastery_level": score,
            "confidence": 0.6  # Baja confianza por parsing heurístico
        }
    
    def _create_default_evaluation_data(self) -> Dict[str, Any]:
        """Crea datos de evaluación por defecto"""
        return {
            "score": 0.5,
            "strengths": [],
            "improvements": ["Requiere evaluación manual"],
            "suggestions": ["Consultar con instructor"],
            "misconceptions": [],
            "key_concepts_understood": [],
            "next_topics": [],
            "mastery_level": 0.5,
            "confidence": 0.3
        }
    
    async def _enrich_evaluation_response(
        self,
        eval_data: Dict[str, Any],
        agent_result: Dict[str, Any],
        request: EvaluationRequest,
        start_time: datetime
    ) -> EvaluationResponse:
        """Enriquece la respuesta con metadatos completos"""
        
        # Generar ID único
        evaluation_id = f"eval_{uuid.uuid4().hex[:12]}"
        
        # Calcular progreso de aprendizaje
        learning_progress = await self._calculate_learning_progress(
            request.user_id,
            request.question_id,
            eval_data["mastery_level"]
        )
        
        # Construir feedback detallado
        feedback = FeedbackDetail(
            strengths=eval_data.get("strengths", []),
            improvements=eval_data.get("improvements", []),
            suggestions=eval_data.get("suggestions", []),
            examples=eval_data.get("examples", [])
        )
        
        # Construir lista de misconceptions
        misconceptions = [
            Misconception(**m) if isinstance(m, dict) else 
            Misconception(
                concept=str(m),
                description="Concepto erróneo detectado",
                severity=0.5,
                correction="Revisar material de estudio"
            )
            for m in eval_data.get("misconceptions", [])
        ]
        
        # Calcular tiempo de procesamiento
        processing_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        # Construir metadatos del agente
        agent_metadata = AgentMetadata(
            reasoning_steps=agent_result.get("reasoning_steps", [
                "PLAN: Analyzed student response and evaluation criteria",
                "EXECUTE: Applied pedagogical evaluation tools",
                "OBSERVE: Validated evaluation completeness",
                "REFLECT: Generated constructive feedback"
            ]),
            tools_used=agent_result.get("tools_used", [
                "analyze_student_response",
                "detect_misconceptions",
                "generate_constructive_feedback"
            ]),
            iterations=agent_result.get("iterations", 3),
            confidence_score=eval_data.get("confidence", 0.8),
            reasoning_quality=self._assess_reasoning_quality(agent_result),
            processing_time_ms=processing_time_ms
        )
        
        return EvaluationResponse(
            evaluation_id=evaluation_id,
            score=eval_data["score"],
            feedback=feedback,
            misconceptions_detected=misconceptions,
            learning_progress=learning_progress,
            agent_metadata=agent_metadata,
            key_concepts_understood=eval_data.get("key_concepts_understood", []),
            next_recommended_topics=eval_data.get("next_topics", []),
            estimated_time_to_mastery=self._estimate_time_to_mastery(
                eval_data["mastery_level"]
            )
        )
    
    async def _calculate_learning_progress(
        self,
        user_id: str,
        question_id: str,
        current_mastery: float
    ) -> LearningProgress:
        """Calcula el progreso de aprendizaje del estudiante"""
        
        # Obtener evaluaciones previas
        previous_evals = await self.evaluation_repository.get_user_evaluations(
            user_id=user_id, question_id=question_id, limit=5
        )
        
        # Calcular mejora
        improvement = 0.0
        trend = "stable"
        
        if previous_evals:
            prev_mastery = previous_evals[0].get("mastery_level", 0.5)
            improvement = current_mastery - prev_mastery
            
            # Determinar tendencia
            if improvement > 0.1:
                trend = "improving"
            elif improvement < -0.1:
                trend = "declining"
        
        return LearningProgress(
            current_mastery=current_mastery,
            improvement=improvement,
            trend=trend,
            confidence_level=0.85  # Alta confianza por evaluación agéntica
        )
    
    def _assess_reasoning_quality(self, agent_result: Dict[str, Any]) -> float:
        """Evalúa la calidad del razonamiento del agente"""
        reasoning_steps = agent_result.get("reasoning_steps", [])
        tools_used = agent_result.get("tools_used", [])
        iterations = agent_result.get("iterations", 0)
        
        quality_score = 0.5  # Base
        
        # Más pasos de razonamiento pedagógico = mejor
        if len(reasoning_steps) >= 4:
            quality_score += 0.2
        
        # Uso de herramientas especializadas = mejor
        if len(tools_used) >= 3:
            quality_score += 0.2
        
        # Iteraciones apropiadas = mejor
        if 2 <= iterations <= 5:
            quality_score += 0.1
        
        return min(1.0, quality_score)
    
    def _estimate_time_to_mastery(self, current_mastery: float) -> int:
        """Estima tiempo en minutos para alcanzar dominio completo"""
        if current_mastery >= 0.9:
            return 10  # Práctica de refuerzo
        elif current_mastery >= 0.7:
            return 30  # Estudio moderado
        elif current_mastery >= 0.5:
            return 60  # Estudio intensivo
        else:
            return 120  # Estudio completo desde básicos
    
    def _create_fallback_evaluation(
        self,
        request: EvaluationRequest,
        error_msg: str,
        start_time: datetime
    ) -> EvaluationResponse:
        """Crea evaluación de fallback cuando el agente falla"""
        
        evaluation_id = f"eval_fallback_{uuid.uuid4().hex[:12]}"
        processing_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        return EvaluationResponse(
            evaluation_id=evaluation_id,
            score=0.5,
            feedback=FeedbackDetail(
                strengths=["Respuesta proporcionada"],
                improvements=["Evaluación automática no disponible"],
                suggestions=["Consultar con instructor para feedback detallado"],
                examples=[]
            ),
            misconceptions_detected=[],
            learning_progress=LearningProgress(
                current_mastery=0.5,
                improvement=0.0,
                trend="stable",
                confidence_level=0.3
            ),
            agent_metadata=AgentMetadata(
                reasoning_steps=[f"ERROR: {error_msg}"],
                tools_used=[],
                iterations=0,
                confidence_score=0.0,
                reasoning_quality=0.0,
                processing_time_ms=processing_time_ms
            ),
            key_concepts_understood=[],
            next_recommended_topics=request.expected_concepts[:2] if request.expected_concepts else [],
            estimated_time_to_mastery=60
        )

    async def get_evaluation_by_id(self, evaluation_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene una evaluación por su ID desde el repositorio.
        """
        logger.info("Fetching evaluation by ID", evaluation_id=evaluation_id)
        evaluation = await self.evaluation_repository.get_evaluation_by_id(evaluation_id)
        if not evaluation:
            logger.warn("Evaluation not found", evaluation_id=evaluation_id)
        return evaluation

    async def get_user_evaluation_history(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Obtiene el historial de evaluaciones de un usuario.
        """
        logger.info("Fetching evaluation history for user", user_id=user_id, limit=limit)
        history = await self.evaluation_repository.get_user_evaluations(user_id, limit=limit)
        return history 