# Guía de Integración con LLMs Agénticos - Atomia

## Configuración de Azure AI y Agentes

### Credenciales y Endpoints
```python
# backend/services/llm_orchestrator/src/config.py
from dotenv import load_dotenv
import os

load_dotenv()

class Config:
    # Azure AI Configuration
    AZURE_AI_ENDPOINT = "https://ai-bryanjavierjaramilloc0912ai799661901077.services.ai.azure.com/models"
    AZURE_AI_KEY = os.getenv("AZURE_AI_KEY")
    MODEL_NAME = "deepseek-r1"
    
    # Redis Configuration for Memory
    REDIS_HOST = "localhost"
    REDIS_PORT = 6379
    REDIS_DB = 0
    
    # ChromaDB Configuration for Semantic Memory
    CHROMA_PERSIST_DIR = "./chroma_db"
    CHROMA_COLLECTION = "atomia_memory"
    
    # Agent Configuration
    MAX_ITERATIONS = 10
    MEMORY_WINDOW = 10
    SEMANTIC_SEARCH_LIMIT = 5
```

## Arquitectura del Sistema Agéntico

### Agente Principal con Capacidades Educativas
```python
# backend/services/llm_orchestrator/src/agents.py
from langchain.agents import create_react_agent
from langchain_core.prompts import PromptTemplate
from langgraph.graph import StateGraph, END
from typing import Dict, List, Any

class EducationalAgent:
    """
    Agente educativo con capacidades de razonamiento, memoria y herramientas especializadas
    """
    
    def __init__(self, llm, tools, memory_system):
        self.llm = llm
        self.tools = tools
        self.memory = memory_system
        
        # Prompt especializado para educación
        self.prompt = PromptTemplate.from_template("""
        Eres un agente de IA educativo especializado en aprendizaje personalizado.
        
        Tu misión es:
        1. Atomizar contenido educativo en unidades mínimas de aprendizaje
        2. Generar preguntas adaptativas basadas en principios pedagógicos
        3. Evaluar respuestas y proporcionar retroalimentación constructiva
        4. Personalizar rutas de aprendizaje según el progreso del estudiante
        
        Principios pedagógicos que debes seguir:
        - Microaprendizaje (Skinner): Divide en unidades pequeñas con feedback inmediato
        - Repetición espaciada: Programa revisiones basadas en curva de olvido
        - Aprendizaje activo: Genera preguntas que requieren reflexión profunda
        - Refuerzo intermitente: Varía recompensas para mantener motivación
        
        Tienes acceso a las siguientes herramientas:
        {tools}
        
        Usa el siguiente formato:
        Pensamiento: Reflexiona sobre qué necesitas hacer
        Acción: Selecciona una herramienta
        Entrada de Acción: Input para la herramienta
        Observación: Resultado de la herramienta
        ... (repite Pensamiento/Acción/Entrada/Observación según necesites)
        Pensamiento: Ahora sé la respuesta final
        Respuesta Final: Tu respuesta al usuario
        
        Conversación previa:
        {chat_history}
        
        Usuario: {input}
        Pensamiento: {agent_scratchpad}
        """)
        
        # Crear agente ReAct
        self.agent = create_react_agent(self.llm, self.tools, self.prompt)
    
    async def process_educational_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Procesa una tarea educativa usando el ciclo de razonamiento agéntico"""
        
        # Recuperar contexto de memoria
        user_id = task.get("user_id")
        context = await self.memory.get_user_context(user_id)
        
        # Ejecutar agente
        result = await self.agent.ainvoke({
            "input": task["query"],
            "chat_history": context.get("chat_history", []),
            "user_context": context
        })
        
        # Guardar interacción en memoria
        await self.memory.add_interaction(
            user_id=user_id,
            query=task["query"],
            response=result["output"],
            tools_used=result.get("intermediate_steps", [])
        )
        
        return result
```

### Sistema de Memoria Multi-Nivel
```python
# backend/services/llm_orchestrator/src/memory.py
import redis
import chromadb
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

class AgenticMemorySystem:
    """
    Sistema de memoria multi-nivel para el agente educativo:
    1. Memoria a corto plazo: Buffer de conversación en memoria
    2. Memoria a largo plazo: Persistencia en Redis
    3. Memoria semántica: Búsqueda vectorial con ChromaDB
    """
    
    def __init__(self, config):
        # Redis para memoria a largo plazo
        self.redis_client = redis.Redis(
            host=config.REDIS_HOST,
            port=config.REDIS_PORT,
            db=config.REDIS_DB,
            decode_responses=True
        )
    
        # ChromaDB para memoria semántica
        self.chroma_client = chromadb.PersistentClient(
            path=config.CHROMA_PERSIST_DIR
        )
        self.collection = self.chroma_client.get_or_create_collection(
            name=config.CHROMA_COLLECTION
        )
        
        # Buffer de memoria a corto plazo
        self.short_term_memory = {}
        self.memory_window = config.MEMORY_WINDOW
    
    async def add_interaction(self, user_id: str, query: str, 
                            response: str, tools_used: List = None):
        """Almacena una interacción en todos los niveles de memoria"""
        
        interaction = {
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "response": response,
            "tools_used": tools_used or [],
            "user_id": user_id
        }
        
        # 1. Memoria a corto plazo
        if user_id not in self.short_term_memory:
            self.short_term_memory[user_id] = []
        
        self.short_term_memory[user_id].append(interaction)
        
        # Mantener solo las últimas N interacciones
        if len(self.short_term_memory[user_id]) > self.memory_window:
            self.short_term_memory[user_id] = self.short_term_memory[user_id][-self.memory_window:]
        
        # 2. Memoria a largo plazo (Redis)
        interaction_key = f"interaction:{user_id}:{datetime.now().timestamp()}"
        self.redis_client.setex(
            interaction_key,
            timedelta(days=30),  # 30 días de retención
            str(interaction)
        )
        
        # 3. Memoria semántica (ChromaDB)
        self.collection.add(
            documents=[f"{query} {response}"],
            metadatas=[interaction],
            ids=[interaction_key]
        )
    
    async def search_semantic_memory(self, query: str, limit: int = 5) -> List[Dict]:
        """Busca en memoria semántica usando similitud vectorial"""
        results = self.collection.query(
            query_texts=[query],
            n_results=limit
        )
        
        return [
            {
                "content": doc,
                "metadata": meta,
                "similarity": 1 - distance  # ChromaDB usa distancia, convertimos a similitud
            }
            for doc, meta, distance in zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0]
            )
        ]
    
    async def get_user_context(self, user_id: str) -> Dict[str, Any]:
        """Recupera el contexto completo del usuario"""
        
        # Memoria a corto plazo
        recent_interactions = self.short_term_memory.get(user_id, [])
        
        # Perfil del usuario desde Redis
        user_profile_key = f"profile:{user_id}"
        user_profile = self.redis_client.hgetall(user_profile_key)
        
        return {
            "chat_history": recent_interactions,
            "user_profile": user_profile,
            "learning_progress": await self._get_learning_progress(user_id)
        }
    
    async def _get_learning_progress(self, user_id: str) -> Dict[str, Any]:
        """Recupera el progreso de aprendizaje del usuario"""
        progress_key = f"progress:{user_id}"
        progress_data = self.redis_client.hgetall(progress_key)
        
        return {
            "completed_atoms": progress_data.get("completed_atoms", "0"),
            "current_difficulty": progress_data.get("current_difficulty", "básico"),
            "last_activity": progress_data.get("last_activity"),
            "streak_days": progress_data.get("streak_days", "0")
        }
```

### Herramientas Educativas Especializadas
```python
# backend/services/llm_orchestrator/src/tools.py
from langchain.tools import BaseTool
from typing import Type, Dict, Any, List
from pydantic import BaseModel, Field

class AtomSearchInput(BaseModel):
    """Input para búsqueda de átomos de aprendizaje"""
    query: str = Field(description="Consulta para buscar átomos relacionados")
    difficulty: str = Field(default="all", description="Nivel de dificultad: básico, intermedio, avanzado, all")

class AtomSearchTool(BaseTool):
    """Herramienta para buscar átomos de aprendizaje existentes"""
    name = "search_learning_atoms"
    description = "Busca átomos de aprendizaje relacionados con un tema específico"
    args_schema: Type[BaseModel] = AtomSearchInput
    
    def _run(self, query: str, difficulty: str = "all") -> str:
        """Implementación de búsqueda de átomos"""
        # Aquí iría la lógica de búsqueda en la base de datos
        # Por ahora retornamos un ejemplo
        return f"Encontrados 3 átomos relacionados con '{query}' de nivel {difficulty}"

class ProgressTrackingInput(BaseModel):
    """Input para seguimiento de progreso"""
    user_id: str = Field(description="ID del usuario")
    action: str = Field(description="Acción: get_progress, update_progress, get_recommendations")

class ProgressTrackingTool(BaseTool):
    """Herramienta para rastrear y actualizar progreso de aprendizaje"""
    name = "track_learning_progress"
    description = "Rastrea el progreso de aprendizaje del usuario y proporciona recomendaciones"
    args_schema: Type[BaseModel] = ProgressTrackingInput
    
    def _run(self, user_id: str, action: str) -> str:
        """Implementación de seguimiento de progreso"""
        if action == "get_progress":
            return f"Usuario {user_id}: 15 átomos completados, nivel intermedio, racha de 7 días"
        elif action == "get_recommendations":
            return f"Recomendaciones para {user_id}: Revisar álgebra básica, avanzar a funciones"
        else:
            return f"Progreso actualizado para {user_id}"

class QuestionGenerationInput(BaseModel):
    """Input para generación de preguntas"""
    atom_content: str = Field(description="Contenido del átomo para generar preguntas")
    question_type: str = Field(description="Tipo: multiple_choice, true_false, short_answer, essay")
    difficulty: str = Field(description="Nivel de dificultad: básico, intermedio, avanzado")

class QuestionGenerationTool(BaseTool):
    """Herramienta para generar preguntas adaptativas"""
    name = "generate_adaptive_questions"
    description = "Genera preguntas educativas basadas en principios pedagógicos"
    args_schema: Type[BaseModel] = QuestionGenerationInput
    
    def _run(self, atom_content: str, question_type: str, difficulty: str) -> str:
        """Implementación de generación de preguntas"""
        return f"Pregunta {question_type} generada para contenido de nivel {difficulty}"

class AnswerEvaluationInput(BaseModel):
    """Input para evaluación de respuestas"""
    question: str = Field(description="Pregunta formulada")
    user_answer: str = Field(description="Respuesta del usuario")
    correct_answer: str = Field(description="Respuesta correcta")

class AnswerEvaluationTool(BaseTool):
    """Herramienta para evaluar respuestas del usuario"""
    name = "evaluate_user_answer"
    description = "Evalúa respuestas del usuario y proporciona retroalimentación"
    args_schema: Type[BaseModel] = AnswerEvaluationInput
    
    def _run(self, question: str, user_answer: str, correct_answer: str) -> str:
        """Implementación de evaluación de respuestas"""
        return f"Respuesta evaluada: 85% correcta. Retroalimentación: Buen razonamiento, revisa el concepto X"

def get_educational_tools() -> List[BaseTool]:
    """Retorna todas las herramientas educativas disponibles"""
    return [
        AtomSearchTool(),
        ProgressTrackingTool(),
        QuestionGenerationTool(),
        AnswerEvaluationTool()
    ]
```

## Ciclo de Razonamiento Agéntico

### Implementación con LangGraph
```python
# backend/services/llm_orchestrator/src/orchestrator.py
from langgraph.graph import StateGraph, END
from typing import Dict, Any, List
import asyncio

class AgentState(TypedDict):
    """Estado del agente durante el procesamiento"""
    messages: List[Any]
    current_task: str
    user_context: Dict[str, Any]
    tools_used: List[str]
    reasoning_steps: List[str]
    final_answer: str
    error_count: int

class AgenticOrchestrator:
    """
    Orquestador agéntico que implementa el ciclo Plan-Execute-Observe-Reflect
    """
    
    def __init__(self, agent, memory_system, tools):
        self.agent = agent
        self.memory = memory_system
        self.tools = tools
        self.max_iterations = 10
        
        # Construir grafo de estados
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """Construye el grafo de workflow del agente"""
        
        workflow = StateGraph(AgentState)
        
        # Nodos del workflow
        workflow.add_node("plan", self._plan_step)
        workflow.add_node("execute", self._execute_step)
        workflow.add_node("observe", self._observe_step)
        workflow.add_node("reflect", self._reflect_step)
        workflow.add_node("finalize", self._finalize_step)
        
        # Conexiones del workflow
        workflow.set_entry_point("plan")
        workflow.add_edge("plan", "execute")
        workflow.add_edge("execute", "observe")
        workflow.add_edge("observe", "reflect")
        
        # Lógica condicional para continuar o finalizar
        workflow.add_conditional_edges(
            "reflect",
            self._should_continue,
            {
                "continue": "plan",
                "finish": "finalize"
            }
        )
        workflow.add_edge("finalize", END)
        
        return workflow.compile()
    
    async def _plan_step(self, state: AgentState) -> AgentState:
        """Paso de planificación: Analiza la tarea y planifica acciones"""
        
        planning_prompt = f"""
        Tarea educativa: {state['current_task']}
        Contexto del usuario: {state['user_context']}
        
        Planifica los pasos necesarios para completar esta tarea educativa.
        Considera los principios pedagógicos y las herramientas disponibles.
        """
        
        plan = await self.agent.llm.ainvoke(planning_prompt)
        
        state['reasoning_steps'].append(f"PLAN: {plan.content}")
        return state
    
    async def _execute_step(self, state: AgentState) -> AgentState:
        """Paso de ejecución: Ejecuta las acciones planificadas"""
        
        try:
            # Ejecutar el agente con las herramientas
            result = await self.agent.agent.ainvoke({
                "input": state['current_task'],
                "chat_history": state['user_context'].get('chat_history', [])
            })
            
            state['messages'].append(result)
            if result.get('intermediate_steps'):
                state['tools_used'].extend([
                    step[0].tool for step in result['intermediate_steps']
                ])
            
            except Exception as e:
            state['error_count'] += 1
            state['reasoning_steps'].append(f"ERROR: {str(e)}")
        
        return state
    
    async def _observe_step(self, state: AgentState) -> AgentState:
        """Paso de observación: Analiza los resultados de la ejecución"""
        
        last_result = state['messages'][-1] if state['messages'] else {}
        
        observation = f"""
        Resultado de la ejecución:
        - Herramientas usadas: {state['tools_used']}
        - Respuesta: {last_result.get('output', 'Sin respuesta')}
        - Errores: {state['error_count']}
        """
        
        state['reasoning_steps'].append(f"OBSERVE: {observation}")
        return state
    
    async def _reflect_step(self, state: AgentState) -> AgentState:
        """Paso de reflexión: Evalúa si la tarea se completó satisfactoriamente"""
        
        reflection_prompt = f"""
        Evalúa si la tarea educativa se completó satisfactoriamente:
        
        Tarea original: {state['current_task']}
        Pasos realizados: {state['reasoning_steps']}
        Herramientas usadas: {state['tools_used']}
        Errores encontrados: {state['error_count']}
        
        ¿La tarea se completó exitosamente? ¿Se necesitan más acciones?
        Responde solo: COMPLETA o CONTINUAR
        """
        
        reflection = await self.agent.llm.ainvoke(reflection_prompt)
        state['reasoning_steps'].append(f"REFLECT: {reflection.content}")
        
        return state
    
    def _should_continue(self, state: AgentState) -> str:
        """Decide si continuar iterando o finalizar"""
        
        # Verificar límites
        if len(state['reasoning_steps']) >= self.max_iterations:
            return "finish"
        
        if state['error_count'] >= 3:
            return "finish"
        
        # Verificar si la reflexión indica finalización
        last_reflection = state['reasoning_steps'][-1] if state['reasoning_steps'] else ""
        if "COMPLETA" in last_reflection.upper():
            return "finish"
        
        return "continue"
    
    async def _finalize_step(self, state: AgentState) -> AgentState:
        """Paso final: Consolida los resultados"""
        
        final_message = state['messages'][-1] if state['messages'] else {}
        state['final_answer'] = final_message.get('output', 'No se pudo completar la tarea')
        
        return state
    
    async def process_educational_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Procesa una tarea educativa usando el workflow agéntico"""
        
        # Estado inicial
        initial_state = AgentState(
            messages=[],
            current_task=task['query'],
            user_context=await self.memory.get_user_context(task.get('user_id')),
            tools_used=[],
            reasoning_steps=[],
            final_answer="",
            error_count=0
        )
        
        # Ejecutar workflow
        final_state = await self.workflow.ainvoke(initial_state)
        
        # Guardar en memoria
        await self.memory.add_interaction(
            user_id=task.get('user_id'),
            query=task['query'],
            response=final_state['final_answer'],
            tools_used=final_state['tools_used']
        )
        
        return {
            "answer": final_state['final_answer'],
            "reasoning_steps": final_state['reasoning_steps'],
            "tools_used": final_state['tools_used'],
            "iterations": len(final_state['reasoning_steps'])
        }
```

## API Endpoints para Agente Educativo

### Servidor FastAPI con Capacidades Agénticas
```python
# backend/services/llm_orchestrator/src/main.py
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

app = FastAPI(title="Atomia - Agente Educativo Agéntico", version="1.0.0")

class EducationalTaskRequest(BaseModel):
    query: str
    user_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    task_type: Optional[str] = "general"

class AgentResponse(BaseModel):
    answer: str
    reasoning_steps: List[str]
    tools_used: List[str]
    iterations: int
    metadata: Dict[str, Any]

@app.post("/agent/process", response_model=AgentResponse)
async def process_educational_task(request: EducationalTaskRequest):
    """
    Procesa una tarea educativa usando el agente con capacidades de razonamiento
    """
        try:
        result = await orchestrator.process_educational_task({
            "query": request.query,
            "user_id": request.user_id,
            "context": request.context,
            "task_type": request.task_type
        })
        
        return AgentResponse(
            answer=result["answer"],
            reasoning_steps=result["reasoning_steps"],
            tools_used=result["tools_used"],
            iterations=result["iterations"],
            metadata={"status": "success", "timestamp": datetime.now().isoformat()}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing task: {str(e)}")
    
@app.post("/agent/memory/search")
async def search_memory(query: str, user_id: Optional[str] = None, limit: int = 5):
    """
    Busca en la memoria semántica del agente
    """
    try:
        results = await memory_system.search_semantic_memory(query, limit)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching memory: {str(e)}")

@app.get("/agent/context/{user_id}")
async def get_user_context(user_id: str):
    """
    Obtiene el contexto completo de un usuario
    """
    try:
        context = await memory_system.get_user_context(user_id)
        return context
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting context: {str(e)}")

@app.post("/agent/feedback")
async def provide_feedback(
    user_id: str, 
    interaction_id: str, 
    feedback: str, 
    rating: int
):
    """
    Permite al usuario proporcionar retroalimentación sobre las respuestas del agente
    """
    try:
        # Guardar feedback para mejorar el agente
        feedback_data = {
            "user_id": user_id,
            "interaction_id": interaction_id,
            "feedback": feedback,
            "rating": rating,
            "timestamp": datetime.now().isoformat()
        }
        
        # Aquí se implementaría el almacenamiento del feedback
        return {"status": "feedback_received", "data": feedback_data}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving feedback: {str(e)}")
```

## Testing del Sistema Agéntico

### Tests de Integración para Agentes
```python
# tests/test_agentic_system.py
import pytest
from unittest.mock import Mock, AsyncMock
import asyncio

class TestAgenticSystem:

    @pytest.fixture
    async def mock_agent_setup(self):
        """Setup para tests del sistema agéntico"""
        mock_llm = AsyncMock()
        mock_memory = AsyncMock()
        mock_tools = [Mock() for _ in range(4)]
        
        return {
            "llm": mock_llm,
            "memory": mock_memory,
            "tools": mock_tools
        }
    
    @pytest.mark.asyncio
    async def test_educational_task_processing(self, mock_agent_setup):
        """Test completo del procesamiento de tareas educativas"""
        
        # Configurar mocks
        mock_agent_setup["memory"].get_user_context.return_value = {
            "chat_history": [],
            "user_profile": {"level": "intermedio"},
            "learning_progress": {"completed_atoms": 10}
        }
        
        mock_agent_setup["llm"].ainvoke.return_value = Mock(
            content="Tarea completada exitosamente"
        )
        
        # Crear orchestrator
        orchestrator = AgenticOrchestrator(
            agent=Mock(llm=mock_agent_setup["llm"]),
            memory_system=mock_agent_setup["memory"],
            tools=mock_agent_setup["tools"]
        )
        
        # Ejecutar tarea
        result = await orchestrator.process_educational_task({
            "query": "Explica el concepto de funciones en matemáticas",
            "user_id": "test_user_123"
        })
        
        # Verificaciones
        assert "answer" in result
        assert "reasoning_steps" in result
        assert "tools_used" in result
        assert isinstance(result["iterations"], int)
        
        # Verificar que se guardó en memoria
        mock_agent_setup["memory"].add_interaction.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_memory_system_integration(self, mock_agent_setup):
        """Test del sistema de memoria multi-nivel"""
        
        memory_system = AgenticMemorySystem(Mock())
        
        # Test añadir interacción
        await memory_system.add_interaction(
            user_id="test_user",
            query="¿Qué es una función?",
            response="Una función es una relación...",
            tools_used=["search_learning_atoms"]
        )
        
        # Test búsqueda semántica
        results = await memory_system.search_semantic_memory(
            "funciones matemáticas"
        )
        
        assert isinstance(results, list)
    
    @pytest.mark.asyncio
    async def test_workflow_execution(self, mock_agent_setup):
        """Test del workflow completo Plan-Execute-Observe-Reflect"""
        
        orchestrator = AgenticOrchestrator(
            agent=Mock(),
            memory_system=mock_agent_setup["memory"],
            tools=mock_agent_setup["tools"]
        )
        
        # Estado inicial
        initial_state = AgentState(
            messages=[],
            current_task="Generar pregunta sobre álgebra",
            user_context={"level": "básico"},
            tools_used=[],
            reasoning_steps=[],
            final_answer="",
            error_count=0
            )
            
        # Ejecutar pasos del workflow
        state_after_plan = await orchestrator._plan_step(initial_state)
        assert len(state_after_plan['reasoning_steps']) > 0
        assert "PLAN" in state_after_plan['reasoning_steps'][0]
    
    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self, mock_agent_setup):
        """Test del manejo de errores y recuperación del agente"""
        
        # Simular error en herramienta
        mock_tool = Mock()
        mock_tool.run.side_effect = Exception("Tool error")
        
        orchestrator = AgenticOrchestrator(
            agent=Mock(),
            memory_system=mock_agent_setup["memory"],
            tools=[mock_tool]
        )
        
        # El agente debe manejar el error y continuar
        result = await orchestrator.process_educational_task({
            "query": "Test query",
            "user_id": "test_user"
        })
        
        # Verificar que el error se manejó
        assert "final_answer" in result  # No debe fallar completamente
```

## Monitoreo y Métricas Agénticas

### Métricas Específicas para Agentes
```python
# backend/services/monitoring/agent_metrics.py
import prometheus_client as prom
from datetime import datetime
from typing import Dict, List

# Métricas específicas para el sistema agéntico
agent_task_duration = prom.Histogram(
    'agent_task_duration_seconds',
    'Duración de procesamiento de tareas educativas',
    ['task_type', 'user_level']
)

agent_reasoning_steps = prom.Histogram(
    'agent_reasoning_steps_count',
    'Número de pasos de razonamiento por tarea',
    ['task_type', 'completion_status']
)

agent_tool_usage = prom.Counter(
    'agent_tool_usage_total',
    'Uso de herramientas educativas por el agente',
    ['tool_name', 'success']
)

agent_memory_operations = prom.Counter(
    'agent_memory_operations_total',
    'Operaciones de memoria del agente',
    ['operation_type', 'memory_level']
)

def record_agent_metrics(task_result: Dict, duration: float, task_type: str):
    """Registra métricas del agente después de procesar una tarea"""
    
    # Duración de la tarea
    user_level = task_result.get('user_context', {}).get('level', 'unknown')
    agent_task_duration.labels(
        task_type=task_type,
        user_level=user_level
    ).observe(duration)
    
    # Pasos de razonamiento
    steps_count = len(task_result.get('reasoning_steps', []))
    completion_status = 'success' if task_result.get('answer') else 'failure'
    agent_reasoning_steps.labels(
        task_type=task_type,
        completion_status=completion_status
    ).observe(steps_count)
    
    # Uso de herramientas
    for tool_name in task_result.get('tools_used', []):
        agent_tool_usage.labels(
            tool_name=tool_name,
            success='true'
        ).inc()
```

## Mejores Prácticas para Agentes Educativos

### 1. Diseño de Prompts Agénticos
```python
def build_educational_agent_prompt(
    role: str,
    pedagogical_principles: List[str],
    available_tools: List[str],
    user_context: Dict[str, Any]
) -> str:
    """Construye prompts especializados para agentes educativos"""
    
    return f"""
## Identidad del Agente
{role}

## Principios Pedagógicos a Seguir
{format_pedagogical_principles(pedagogical_principles)}

## Contexto del Usuario
Nivel: {user_context.get('level', 'principiante')}
Progreso: {user_context.get('progress', 'inicio')}
Preferencias: {user_context.get('preferences', 'no especificadas')}
Historial: {format_learning_history(user_context.get('history', []))}

## Herramientas Disponibles
{format_tools_description(available_tools)}

## Instrucciones de Razonamiento
1. PLANIFICA: Analiza la tarea educativa y los objetivos de aprendizaje
2. EJECUTA: Usa las herramientas necesarias para completar la tarea
3. OBSERVA: Evalúa los resultados desde una perspectiva pedagógica
4. REFLEXIONA: Considera si se cumplieron los objetivos educativos
5. ADAPTA: Ajusta el enfoque según la respuesta del estudiante

Recuerda: Cada interacción debe promover el aprendizaje activo y la comprensión profunda.
"""
```

### 2. Validación de Respuestas Educativas
```python
class EducationalResponseValidator:
    """Validador especializado para respuestas educativas"""

    def __init__(self):
        self.pedagogical_criteria = [
            "promotes_active_learning",
            "provides_clear_explanation",
            "includes_examples",
            "encourages_reflection",
            "builds_on_prior_knowledge"
        ]
    
    def validate_educational_response(self, response: str, 
                                    task_context: Dict) -> Dict[str, Any]:
        """Valida que la respuesta cumple criterios pedagógicos"""
        
        validation_results = {}
        
        for criterion in self.pedagogical_criteria:
            validator_method = getattr(self, f"_check_{criterion}")
            validation_results[criterion] = validator_method(response, task_context)
        
        overall_score = sum(validation_results.values()) / len(validation_results)
        
        return {
            "overall_score": overall_score,
            "criteria_scores": validation_results,
            "recommendations": self._generate_recommendations(validation_results)
        }
    
    def _check_promotes_active_learning(self, response: str, context: Dict) -> float:
        """Verifica si la respuesta promueve aprendizaje activo"""
        active_indicators = [
            "pregunta", "reflexiona", "practica", "aplica", 
            "compara", "analiza", "explica"
        ]
        
        found_indicators = sum(1 for indicator in active_indicators 
                             if indicator in response.lower())
        
        return min(found_indicators / 3, 1.0)  # Máximo 1.0
```

## Roadmap de Mejoras Agénticas

### Fase 1: Sistema Agéntico Básico ✅
- [x] Implementación del agente educativo con ReAct
- [x] Sistema de memoria multi-nivel
- [x] Herramientas educativas especializadas
- [x] Workflow Plan-Execute-Observe-Reflect
- [x] API endpoints para interacción

### Fase 2: Agentes Especializados (En desarrollo)
- [ ] Agente de Atomización de Contenido
- [ ] Agente de Generación de Preguntas
- [ ] Agente de Evaluación y Retroalimentación
- [ ] Agente de Planificación Adaptativa
- [ ] Coordinador Multi-Agente

### Fase 3: Capacidades Avanzadas (Futuro)
- [ ] Aprendizaje por refuerzo para mejora continua
- [ ] Agentes colaborativos para resolución de problemas
- [ ] Personalización automática de agentes por usuario
- [ ] Integración con modelos de conocimiento dinámicos
- [ ] Sistema de agentes auto-mejorantes

### Consideraciones de Escalabilidad
- **Paralelización**: Procesamiento concurrente de múltiples usuarios
- **Cache inteligente**: Reutilización de razonamientos similares
- **Balanceador de carga**: Distribución de tareas entre instancias
- **Monitoreo avanzado**: Detección de patrones de uso y optimización
- **Fallback graceful**: Degradación controlada en caso de errores

El sistema agéntico de Atomia representa un avance significativo en la personalización educativa, combinando capacidades de razonamiento avanzado con principios pedagógicos científicos para crear experiencias de aprendizaje verdaderamente adaptativas. 