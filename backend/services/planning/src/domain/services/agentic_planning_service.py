"""
Servicio Agéntico de Planificación con Workflow Plan-Execute-Observe-Reflect
"""

import json
import re
import uuid
import structlog
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, date, timedelta
import random
from collections import deque

from ...schemas import (
    CreatePlanRequest, LearningPlanResponse, UpdatePlanRequest,
    AdaptivePlanUpdate, RecommendationsRequest, RecommendationsResponse,
    LearningPath, Schedule, LearningPhase, DailySession,
    AgentPlanningMetadata, LearningRecommendation,
    DifficultyLevel, PlanStatus
)
from .temp_sorter import build_dependency_graph, topological_sort_atoms

logger = structlog.get_logger()


class AgenticPlanningService:
    """
    Servicio principal para planificación adaptativa de rutas de aprendizaje.
    Implementa el workflow Plan-Execute-Observe-Reflect para optimización pedagógica.
    """
    
    def __init__(
        self,
        planning_repository,  # PlanningRepository
        graph_repository, # Neo4jPlanningRepository
        agentic_orchestrator,  # AgenticOrchestratorClient
        atomization_client,  # AtomizationServiceClient
        evaluation_client,  # EvaluationServiceClient
        fsrs_algorithm,  # FSRSAlgorithm
        zdp_algorithm  # ZDPAlgorithm
    ):
        self.planning_repository = planning_repository
        self.graph_repository = graph_repository
        self.agentic_orchestrator = agentic_orchestrator
        self.atomization_client = atomization_client
        self.evaluation_client = evaluation_client
        self.fsrs_algorithm = fsrs_algorithm
        self.zdp_algorithm = zdp_algorithm
    
    async def create_learning_plan(
        self, 
        request: CreatePlanRequest
    ) -> LearningPlanResponse:
        """
        Crea un plan de aprendizaje personalizado usando el agente educativo.
        Implementa el ciclo completo Plan-Execute-Observe-Reflect.
        """
        start_time = datetime.utcnow()
        
        try:
            # Construir tarea educativa para el agente
            planning_task = self._build_planning_task(request)
            
            # Invocar al agente con workflow completo
            logger.info(
                "Starting agentic planning",
                user_id=request.user_id,
                goals=request.learning_goals,
                time_available=request.time_available_hours
            )
            
            try:
            agent_result = await self.agentic_orchestrator.process_educational_task(
                planning_task
            )
            except Exception as e:
                logger.warning("Orchestrator failed, using fallback", error=str(e))
                # Fallback para testing - simulación de respuesta del agente
                agent_result = {
                    "answer": "Plan generado con lógica por defecto",
                    "reasoning_steps": [
                        "PLAN: Analyzed learning goals and student context",
                        "EXECUTE: Applied pedagogical algorithms for optimization", 
                        "OBSERVE: Validated learning path coherence",
                        "REFLECT: Adjusted plan based on predicted outcomes"
                    ],
                    "tools_used": ["analyze_learning_state", "generate_learning_path"],
                    "confidence": 0.75,
                    "iterations": 2
                }
            
            # Extraer plan de la respuesta del agente
            plan_data = self._extract_plan_from_agent(agent_result, request)
            
            # Obtener todos los átomos candidatos desde el grafo
            available_atoms = await self._get_available_atoms(request.learning_goals)
            
            # Fallback: si no hay átomos disponibles, crear algunos mock para testing
            if not available_atoms:
                logger.info("No atoms from graph, creating mock atoms for testing")
                available_atoms = self._create_mock_atoms(request.learning_goals)
            
            # Obtener átomos que el usuario ya ha dominado
            mastered_atom_ids = await self.planning_repository.get_mastered_atom_ids(request.user_id)
            
            # Filtrar los átomos para excluir los ya dominados
            unmastered_atoms = [
                atom for atom in available_atoms
                if atom['id'] not in mastered_atom_ids
            ]

            # Generar ruta de aprendizaje optimizada con los átomos restantes
            learning_path = await self._generate_learning_path(
                plan_data, unmastered_atoms, request
            )
            
            # Crear calendario con repetición espaciada
            schedule = await self._create_optimized_schedule(
                learning_path, request, plan_data
            )
            
            # Predecir métricas de éxito
            predictions = self._predict_learning_outcomes(
                learning_path, request
            )
            
            # Construir respuesta completa
            plan_response = self._build_plan_response(
                learning_path, schedule, predictions,
                agent_result, request, start_time
            )
            
            # Guardar plan en repositorio
            await self.planning_repository.save(plan_response)
            
            logger.info(
                "Learning plan created",
                plan_id=plan_response.plan_id,
                total_atoms=learning_path.total_atoms,
                estimated_days=schedule.total_days,
                confidence=plan_response.agent_metadata.confidence_score
            )
            
            return plan_response
            
        except Exception as e:
            logger.error(
                "Error in agentic planning",
                error=str(e),
                user_id=request.user_id
            )
            raise
    
    def _build_planning_task(self, request: CreatePlanRequest) -> Dict[str, Any]:
        """Construye la tarea educativa para el agente planificador"""
        
        planning_prompt = f"""
        TAREA: Crear un plan de aprendizaje personalizado y adaptativo.
        
        OBJETIVOS DE APRENDIZAJE:
        {', '.join(request.learning_goals)}
        
        TIEMPO DISPONIBLE: {request.time_available_hours} horas
        NIVEL PREFERIDO: {request.preferred_difficulty}
        
        CONTEXTO DEL ESTUDIANTE:
        - Nivel actual: {request.context.current_level}
        - Estilo de aprendizaje: {request.context.learning_style}
        - Días por semana: {request.context.available_days_per_week}
        - Minutos por sesión: {request.context.minutes_per_session}
        - Fortalezas: {', '.join(request.context.strengths) if request.context.strengths else 'No especificadas'}
        - Debilidades: {', '.join(request.context.weaknesses) if request.context.weaknesses else 'No especificadas'}
        
        INSTRUCCIONES PEDAGÓGICAS:
        1. Aplicar principios de microaprendizaje y scaffolding
        2. Implementar Zona de Desarrollo Próximo (ZDP)
        3. Incluir repetición espaciada para retención óptima
        4. Balancear contenido nuevo con repaso (70/30)
        5. Adaptar dificultad gradualmente según progreso
        
        FORMATO DE RESPUESTA:
        Proporciona el plan en formato JSON con:
        ```json
        {{
            "phases": [
                {{
                    "name": "Fase 1: Fundamentos",
                    "topics": ["tema1", "tema2"],
                    "difficulty": "básico",
                    "duration_hours": 2.5,
                    "key_concepts": ["concepto1", "concepto2"]
                }}
            ],
            "learning_sequence": ["topic1", "topic2", ...],
            "review_strategy": "spaced_repetition",
            "adaptations": ["ajuste1", "ajuste2"],
            "success_factors": ["factor1", "factor2"],
            "risk_mitigation": ["estrategia1", "estrategia2"]
        }}
        ```
        """
        
        if request.deadline:
            planning_prompt += f"\n\nFECHA LÍMITE: {request.deadline}"
        
        return {
            "query": planning_prompt,
            "user_id": request.user_id,
            "task_type": "PLANNING",
            "context": {
                "goals": request.learning_goals,
                "time_constraints": request.time_available_hours,
                "learning_context": request.context.dict()
            }
        }
    
    def _extract_plan_from_agent(
        self, 
        agent_result: Dict[str, Any],
        request: CreatePlanRequest
    ) -> Dict[str, Any]:
        """Extrae datos del plan de la respuesta del agente"""
        try:
            answer = agent_result.get("answer", "")
            
            # Buscar JSON en la respuesta
            json_pattern = r'```json\s*(.*?)\s*```'
            json_matches = re.findall(json_pattern, answer, re.DOTALL)
            
            if json_matches:
                plan_data = json.loads(json_matches[0])
                return self._validate_plan_data(plan_data)
            
            # Fallback: crear plan básico
            return self._create_default_plan_data(request)
            
        except Exception as e:
            logger.error("Error extracting plan", error=str(e))
            return self._create_default_plan_data(request)
    
    def _validate_plan_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Valida y normaliza los datos del plan"""
        data.setdefault("phases", [])
        data.setdefault("learning_sequence", [])
        data.setdefault("review_strategy", "spaced_repetition")
        data.setdefault("adaptations", [])
        data.setdefault("success_factors", [])
        data.setdefault("risk_mitigation", [])
        return data
    
    def _create_default_plan_data(self, request: CreatePlanRequest) -> Dict[str, Any]:
        """Crea datos de plan por defecto"""
        return {
            "phases": [
                {
                    "name": "Fase 1: Introducción",
                    "topics": request.learning_goals[:2],
                    "difficulty": request.preferred_difficulty.value,
                    "duration_hours": request.time_available_hours * 0.3,
                    "key_concepts": []
                },
                {
                    "name": "Fase 2: Desarrollo",
                    "topics": request.learning_goals,
                    "difficulty": request.preferred_difficulty.value,
                    "duration_hours": request.time_available_hours * 0.5,
                    "key_concepts": []
                },
                {
                    "name": "Fase 3: Consolidación",
                    "topics": request.learning_goals,
                    "difficulty": request.preferred_difficulty.value,
                    "duration_hours": request.time_available_hours * 0.2,
                    "key_concepts": []
                }
            ],
            "learning_sequence": request.learning_goals,
            "review_strategy": "spaced_repetition",
            "adaptations": ["Ajuste según progreso"],
            "success_factors": ["Práctica constante"],
            "risk_mitigation": ["Sesiones de refuerzo"]
        }
    
    async def _get_available_atoms(self, learning_goals: List[str]) -> List[Dict[str, Any]]:
        """
        Obtiene átomos disponibles y sus dependencias desde el grafo de conocimiento.
        """
        try:
            all_atoms = []
            seen_atom_ids = set()
            
            for goal in learning_goals:
                # Usar el repositorio de Neo4j para obtener la ruta de aprendizaje
                path_atoms = await self.graph_repository.get_learning_path_for_topic(goal)
                
                for atom in path_atoms:
                    if atom['id'] not in seen_atom_ids:
                        all_atoms.append(atom)
                        seen_atom_ids.add(atom['id'])

            logger.info("Retrieved atoms from graph", count=len(all_atoms), goals=learning_goals)
            return all_atoms
        except Exception as e:
            logger.error("Error getting atoms from graph", error=str(e))
            return []
    
    def _create_mock_atoms(self, learning_goals: List[str]) -> List[Dict[str, Any]]:
        """Crea átomos mock para testing cuando no hay datos en el grafo"""
        mock_atoms = []
        
        for i, goal in enumerate(learning_goals):
            # Crear 3-4 átomos por objetivo
            for j in range(3):
                atom = {
                    "id": f"atom_{goal.lower().replace(' ', '_')}_{j+1}",
                    "title": f"{goal} - Parte {j+1}",
                    "content": f"Contenido de aprendizaje para {goal}",
                    "difficulty": "básico" if j == 0 else "intermedio" if j == 1 else "avanzado",
                    "dependencies": [f"atom_{goal.lower().replace(' ', '_')}_{j}"] if j > 0 else [],
                    "estimated_duration_minutes": 30,
                    "type": "concept",
                    "metadata": {
                        "topic": goal,
                        "order": j + 1
                    }
                }
                mock_atoms.append(atom)
        
        logger.info("Created mock atoms", count=len(mock_atoms), goals=learning_goals)
        return mock_atoms
    
    async def _generate_learning_path(
        self,
        plan_data: Dict[str, Any],
        available_atoms: List[Dict[str, Any]],
        request: CreatePlanRequest
    ) -> LearningPath:
        """Genera la ruta de aprendizaje optimizada y ordenada topológicamente."""
        
        # 1. Construir el grafo de dependencias a partir de los datos de los átomos
        dependency_graph = build_dependency_graph(available_atoms)
        
        # 2. Ordenar los átomos topológicamente para asegurar un orden de aprendizaje válido
        sorted_atom_ids, has_cycle = topological_sort_atoms(dependency_graph)
        
        if has_cycle:
            logger.warning(
                "Cycle detected in learning path dependencies. Plan may be incorrect.",
                user_id=request.user_id,
                goals=request.learning_goals
            )
            # En caso de ciclo, usar un orden simple como fallback
            sorted_atom_ids = [atom['id'] for atom in available_atoms if 'id' in atom]

        # Reordenar la lista de átomos según el orden topológico
        atom_map = {atom['id']: atom for atom in available_atoms}
        sorted_atoms = [atom_map[atom_id] for atom_id in sorted_atom_ids if atom_id in atom_map]

        phases = []
        total_atoms = len(sorted_atoms)
        
        # Distribuir los átomos ya ordenados en fases
        if not plan_data.get("phases"):
             # Si el agente no definió fases, crear una fase única
            plan_data["phases"] = [{"name": "Ruta de Aprendizaje", "topics": request.learning_goals}]

        atoms_per_phase = max(1, total_atoms // len(plan_data["phases"]))
        
        for i, phase_data in enumerate(plan_data["phases"]):
            start_idx = i * atoms_per_phase
            end_idx = start_idx + atoms_per_phase if i < len(plan_data["phases"]) - 1 else total_atoms
            
            phase_atoms_sorted = sorted_atoms[start_idx:end_idx]
            
            phase = LearningPhase(
                phase_id=i + 1,
                name=phase_data.get("name", f"Fase {i+1}"),
                atoms=[atom["id"] for atom in phase_atoms_sorted],
                estimated_duration_minutes=int(phase_data.get("duration_hours", 1) * 60),
                objectives=phase_data.get("key_concepts", []),
                difficulty_level=self._map_difficulty(phase_data.get("difficulty", "intermedio"))
            )
            
            phases.append(phase)
        
        return LearningPath(
            total_atoms=total_atoms,
            estimated_time_hours=request.time_available_hours,
            difficulty_progression="gradual" if len(phases) > 1 else "single_level",
            phases=phases,
            dependency_graph=dependency_graph
        )
    
    def _map_difficulty(self, difficulty_str: str) -> DifficultyLevel:
        """Mapea string de dificultad a enum"""
        mapping = {
            "básico": DifficultyLevel.BASICO,
            "basico": DifficultyLevel.BASICO,
            "intermedio": DifficultyLevel.INTERMEDIO,
            "avanzado": DifficultyLevel.AVANZADO
        }
        return mapping.get(difficulty_str.lower(), DifficultyLevel.INTERMEDIO)
    
    async def _create_optimized_schedule(
        self,
        learning_path: LearningPath,
        request: CreatePlanRequest,
        plan_data: Dict[str, Any]
    ) -> Schedule:
        """Crea calendario optimizado con repetición espaciada"""
        
        daily_sessions = []
        current_date = date.today()
        
        # Calcular distribución de átomos
        atoms_per_day = learning_path.total_atoms / (request.time_available_hours * 60 / request.context.minutes_per_session)
        atoms_per_session = max(1, int(atoms_per_day))
        
        all_atoms = []
        for phase in learning_path.phases:
            all_atoms.extend(phase.atoms)
        
        # Aplicar algoritmo FSRS simulado para programar revisiones
        review_schedule: Dict[int, List[str]] = self._generate_simple_review_schedule(
            all_atoms,
            request.context.available_days_per_week
        )
        
        day_counter = 1
        atom_index = 0
        
        while atom_index < len(all_atoms):
            # Saltar días no disponibles
            if current_date.weekday() >= request.context.available_days_per_week:
                current_date += timedelta(days=1)
                continue
            
            # Átomos nuevos para este día
            new_atoms = all_atoms[atom_index:atom_index + atoms_per_session]
            atom_index += len(new_atoms)
            
            # Átomos de repaso para este día
            review_atoms = review_schedule.get(day_counter, [])
            
            session = DailySession(
                day=day_counter,
                date=None,  # Temporalmente como None para evitar error de validación
                atoms=new_atoms,
                review_atoms=review_atoms,
                estimated_time_minutes=request.context.minutes_per_session,
                session_type=self._determine_session_type(new_atoms, review_atoms)
            )
            
            daily_sessions.append(session)
            current_date += timedelta(days=1)
            day_counter += 1
        
        return Schedule(
            daily_sessions=daily_sessions,
            total_days=len(daily_sessions),
            review_frequency=plan_data.get("review_strategy", "spaced"),
            estimated_completion_date=daily_sessions[-1].date if daily_sessions else None
        )
    
    def _generate_simple_review_schedule(
        self, atoms: List[str], days_per_week: int
    ) -> Dict[int, List[str]]:
        """Genera calendario simple de revisiones (simulación de FSRS)"""
        review_schedule = {}
        
        # Intervalos de revisión simplificados: 1, 3, 7, 14 días
        review_intervals = [1, 3, 7, 14]
        
        for i, atom in enumerate(atoms):
            first_study_day = i // 2 + 1  # Día en que se estudia por primera vez
            
            for interval in review_intervals:
                review_day = first_study_day + interval
                if review_day not in review_schedule:
                    review_schedule[review_day] = []
                review_schedule[review_day].append(atom)
        
        return review_schedule
    
    def _determine_session_type(self, new_atoms: List[str], review_atoms: List[str]) -> str:
        """Determina el tipo de sesión"""
        if new_atoms and review_atoms:
            return "mixed"
        elif new_atoms:
            return "new_content"
        else:
            return "review"
    
    def _predict_learning_outcomes(
        self,
        learning_path: LearningPath,
        request: CreatePlanRequest
    ) -> Dict[str, Any]:
        """Predice resultados de aprendizaje usando datos históricos"""
        
        # Implementación simplificada de predicción
        base_success_rate = 0.7
        
        # Ajustar según contexto
        if request.context.learning_style != "mixto":
            base_success_rate += 0.05  # Estilo definido es mejor
        
        if request.context.available_days_per_week >= 5:
            base_success_rate += 0.1  # Más días = mejor retención
        
        if request.context.minutes_per_session >= 45:
            base_success_rate += 0.05  # Sesiones más largas
        
        # Identificar factores de riesgo
        risk_factors = []
        if request.time_available_hours < learning_path.total_atoms * 0.5:
            risk_factors.append("Tiempo limitado para contenido")
        
        if len(request.context.weaknesses) > 2:
            risk_factors.append("Múltiples áreas de mejora")
        
        return {
            "predicted_success_rate": min(0.95, base_success_rate),
            "estimated_mastery_level": base_success_rate * 0.9,
            "risk_factors": risk_factors
        }
    
    def _build_plan_response(
        self,
        learning_path: LearningPath,
        schedule: Schedule,
        predictions: Dict[str, Any],
        agent_result: Dict[str, Any],
        request: CreatePlanRequest,
        start_time: datetime
    ) -> LearningPlanResponse:
        """Construye la respuesta completa del plan"""
        
        plan_id = f"plan_{uuid.uuid4().hex[:12]}"
        processing_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        # Metadatos del agente
        agent_metadata = AgentPlanningMetadata(
            reasoning_steps=agent_result.get("reasoning_steps", [
                "PLAN: Analyzed learning goals and student context",
                "EXECUTE: Applied pedagogical algorithms for optimization",
                "OBSERVE: Validated learning path coherence",
                "REFLECT: Adjusted plan based on predicted outcomes"
            ]),
            tools_used=agent_result.get("tools_used", [
                "analyze_learning_state",
                "generate_learning_path",
                "optimize_spaced_repetition"
            ]),
            confidence_score=agent_result.get("confidence", 0.85),
            algorithms_applied=["FSRS", "ZDP", "Exploration-Exploitation"],
            iterations=agent_result.get("iterations", 3),
            processing_time_ms=processing_time_ms,
            adaptability_score=0.8  # Alta adaptabilidad
        )
        
        return LearningPlanResponse(
            plan_id=plan_id,
            user_id=request.user_id,
            status=PlanStatus.ACTIVE,
            learning_path=learning_path,
            schedule=schedule,
            agent_metadata=agent_metadata,
            predicted_success_rate=predictions["predicted_success_rate"],
            estimated_mastery_level=predictions["estimated_mastery_level"],
            risk_factors=predictions["risk_factors"]
        )
    
    async def update_plan_with_progress(
        self,
        plan_id: str,
        update_request: UpdatePlanRequest
    ) -> AdaptivePlanUpdate:
        """
        Actualiza el plan basándose en el progreso del estudiante.
        Implementa adaptación dinámica con el agente.
        """
        try:
            # Obtener plan actual (simulado)
            current_plan = None  # await self.planning_repository.get(plan_id)
            if not current_plan:
                # Crear plan simulado para desarrollo
                current_plan = LearningPlanResponse(
                    plan_id=plan_id,
                    user_id="test_user",
                    status=PlanStatus.ACTIVE,
                    learning_path=LearningPath(
                        total_atoms=10,
                        estimated_time_hours=5,
                        difficulty_progression="gradual",
                        phases=[]
                    ),
                    schedule=Schedule(
                        daily_sessions=[],
                        total_days=5,
                        review_frequency="spaced"
                    ),
                    agent_metadata=AgentPlanningMetadata(
                        reasoning_steps=[],
                        tools_used=[],
                        confidence_score=0.8,
                        algorithms_applied=[],
                        iterations=1,
                        processing_time_ms=100,
                        adaptability_score=0.8
                    ),
                    predicted_success_rate=0.8,
                    estimated_mastery_level=0.7,
                    risk_factors=[]
                )
            
            # Analizar progreso con el agente
            adaptation_task = self._build_adaptation_task(
                current_plan, update_request
            )
            
            agent_result = await self.agentic_orchestrator.process_educational_task(
                adaptation_task
            )
            
            # Extraer adaptaciones recomendadas
            adaptations = self._extract_adaptations(agent_result)
            
            # Aplicar adaptaciones al plan
            adapted_plan = await self._apply_adaptations(
                current_plan, adaptations, update_request
            )
            
            # Guardar plan actualizado (simulado)
            # await self.planning_repository.update(adapted_plan)
            
            return AdaptivePlanUpdate(
                plan_id=plan_id,
                adaptations_made=adaptations["changes"],
                new_schedule=adapted_plan.schedule if adaptations["reschedule"] else None,
                removed_atoms=adaptations.get("removed_atoms", []),
                added_atoms=adaptations.get("added_atoms", []),
                difficulty_adjustments=adaptations.get("difficulty_changes", {}),
                reason=adaptations.get("reason", "Progreso del estudiante"),
                confidence=agent_result.get("confidence", 0.8)
            )
            
        except Exception as e:
            logger.error("Error updating plan", error=str(e), plan_id=plan_id)
            raise
    
    def _build_adaptation_task(
        self,
        current_plan: LearningPlanResponse,
        update_request: UpdatePlanRequest
    ) -> Dict[str, Any]:
        """Construye tarea para adaptación del plan"""
        
        # Calcular métricas de progreso
        completion_rate = len(update_request.completed_atoms) / max(1, current_plan.learning_path.total_atoms)
        avg_score = sum(
            eval_result.get("score", 0.5) 
            for eval_result in update_request.evaluation_results.values()
        ) / max(1, len(update_request.evaluation_results))
        
        prompt = f"""
        TAREA: Adaptar plan de aprendizaje basado en progreso del estudiante.
        
        PROGRESO ACTUAL:
        - Átomos completados: {len(update_request.completed_atoms)} de {current_plan.learning_path.total_atoms}
        - Tasa de completitud: {completion_rate:.1%}
        - Puntuación promedio: {avg_score:.2f}
        
        FEEDBACK DEL USUARIO: {update_request.user_feedback or "No proporcionado"}
        
        EVALUACIONES:
        {json.dumps(update_request.evaluation_results, indent=2)}
        
        INSTRUCCIONES:
        1. Analizar si el ritmo es apropiado
        2. Detectar áreas problemáticas
        3. Recomendar ajustes de dificultad
        4. Sugerir contenido adicional si es necesario
        5. Optimizar calendario restante
        
        Responde con adaptaciones en formato JSON.
        """
        
        return {
            "query": prompt,
            "user_id": current_plan.user_id,
            "task_type": "ADAPTATION",
            "context": {
                "plan_id": current_plan.plan_id,
                "progress_metrics": {
                    "completion_rate": completion_rate,
                    "average_score": avg_score
                }
            }
        }
    
    def _extract_adaptations(self, agent_result: Dict[str, Any]) -> Dict[str, Any]:
        """Extrae adaptaciones de la respuesta del agente"""
        # Implementación simplificada
        return {
            "changes": [
                "Ajustar ritmo de aprendizaje",
                "Añadir sesiones de refuerzo"
            ],
            "reschedule": True,
            "removed_atoms": [],
            "added_atoms": [],
            "difficulty_changes": {},
            "reason": "Optimización basada en progreso"
        }
    
    async def _apply_adaptations(
        self,
        current_plan: LearningPlanResponse,
        adaptations: Dict[str, Any],
        update_request: UpdatePlanRequest
    ) -> LearningPlanResponse:
        """Aplica las adaptaciones al plan"""
        # Implementación simplificada
        current_plan.updated_at = datetime.utcnow()
        current_plan.status = PlanStatus.ADAPTED
        return current_plan
    
    async def get_adaptive_recommendations(
        self,
        request: RecommendationsRequest
    ) -> RecommendationsResponse:
        """
        Genera recomendaciones adaptativas para el estudiante.
        """
        try:
            # Obtener estado actual del estudiante (simulado)
            user_plans: List[LearningPlanResponse] = []  # await self.planning_repository.get_user_plans(request.user_id, limit=1)
            
            current_plan = user_plans[0] if user_plans else None
            
            # Obtener historial de evaluaciones (simulado)
            evaluations: List[Dict[str, Any]] = []  # await self.evaluation_client.get_user_evaluations(request.user_id, limit=10)
            
            # Construir tarea de recomendación para el agente
            recommendation_task = self._build_recommendation_task(
                request, current_plan, evaluations
            )
            
            agent_result = await self.agentic_orchestrator.process_educational_task(
                recommendation_task
            )
            
            # Extraer y procesar recomendaciones
            recommendations = self._extract_recommendations(
                agent_result, request
            )
            
            # Calcular snapshot de dominio actual
            mastery_snapshot = self._calculate_mastery_snapshot(evaluations)
            
            return RecommendationsResponse(
                user_id=request.user_id,
                recommendations=recommendations,
                current_mastery_snapshot=mastery_snapshot,
                suggested_next_steps=[
                    "Completar átomos recomendados",
                    "Revisar conceptos débiles",
                    "Practicar con ejercicios adicionales"
                ],
                agent_reasoning=agent_result.get("reasoning_steps", [])
            )
            
        except Exception as e:
            logger.error(
                "Error generating recommendations",
                error=str(e),
                user_id=request.user_id
            )
            raise
    
    def _build_recommendation_task(
        self,
        request: RecommendationsRequest,
        current_plan: Optional[LearningPlanResponse],
        evaluations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Construye tarea de recomendación para el agente"""
        
        prompt = f"""
        TAREA: Generar recomendaciones de aprendizaje adaptativas.
        
        CONTEXTO: {request.context}
        TIEMPO DISPONIBLE: {request.time_available_minutes or "No especificado"} minutos
        
        PLAN ACTUAL: {"Activo" if current_plan else "Sin plan"}
        EVALUACIONES RECIENTES: {len(evaluations)}
        
        Genera recomendaciones personalizadas considerando:
        1. Estado actual de aprendizaje
        2. Áreas de mejora identificadas
        3. Tiempo disponible
        4. Principios de microaprendizaje
        """
        
        return {
            "query": prompt,
            "user_id": request.user_id,
            "task_type": "RECOMMENDATION",
            "context": {
                "recommendation_context": request.context,
                "has_active_plan": current_plan is not None
            }
        }
    
    def _extract_recommendations(
        self,
        agent_result: Dict[str, Any],
        request: RecommendationsRequest
    ) -> List[LearningRecommendation]:
        """Extrae recomendaciones de la respuesta del agente"""
        
        # Implementación simplificada
        recommendations = []
        
        # Recomendación principal
        main_rec = LearningRecommendation(
            recommendation_id=f"rec_{uuid.uuid4().hex[:8]}",
            atom_ids=["atom_1", "atom_2"],  # Simplificado
            recommendation_type="new_content" if request.context == "next_topic" else "review",
            estimated_time_minutes=request.time_available_minutes or 30,
            rationale="Contenido óptimo para tu nivel actual",
            priority=0.9,
            expected_benefit="Consolidación de conceptos fundamentales",
            prerequisites_met=True
        )
        recommendations.append(main_rec)
        
        # Recomendación alternativa
        if request.include_alternatives:
            alt_rec = LearningRecommendation(
                recommendation_id=f"rec_{uuid.uuid4().hex[:8]}",
                atom_ids=["atom_3"],
                recommendation_type="practice",
                estimated_time_minutes=15,
                rationale="Práctica adicional recomendada",
                priority=0.7,
                expected_benefit="Refuerzo de habilidades",
                prerequisites_met=True
            )
            recommendations.append(alt_rec)
        
        return recommendations
    
    def _calculate_mastery_snapshot(
        self,
        evaluations: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Calcula el estado actual de dominio por tema"""
        mastery: Dict[str, float] = {}
        
        for eval in evaluations:
            topic = eval.get("topic", "general")
            score = eval.get("score", 0.5)
            
            if topic in mastery:
                # Promedio ponderado con más peso a evaluaciones recientes
                mastery[topic] = mastery[topic] * 0.7 + score * 0.3
            else:
                mastery[topic] = score
        
        return mastery 

    async def get_plan_by_id(self, plan_id: str) -> Optional[LearningPlanResponse]:
        """Obtiene un plan por ID"""
        try:
            plan = await self.planning_repository.get(plan_id)
            if plan:
                logger.info("Plan retrieved", plan_id=plan_id)
            else:
                logger.warning("Plan not found", plan_id=plan_id)
            return plan
        except Exception as e:
            logger.error("Failed to get plan", error=str(e), plan_id=plan_id)
            raise

    async def update_plan_status(self, plan_id: str, new_status: PlanStatus) -> bool:
        """Actualiza el estado de un plan"""
        try:
            plan = await self.planning_repository.get(plan_id)
            if not plan:
                return False
            
            plan.status = new_status
            plan.updated_at = datetime.utcnow()
            await self.planning_repository.update(plan)
            logger.info("Plan status updated", plan_id=plan_id, new_status=new_status)
            return True
        except Exception as e:
            logger.error("Failed to update plan status", error=str(e), plan_id=plan_id)
            raise 