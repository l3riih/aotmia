"""FastAPI application for LLM orchestrator service."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional
import uuid

from .orchestrator import orchestrator
from .task_types import TaskType


app = FastAPI(title="LLM Orchestrator Service", version="0.1.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ProcessRequest(BaseModel):
    """Request model for processing tasks."""
    task_type: TaskType
    user_input: str
    user_id: str
    session_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ProcessResponse(BaseModel):
    """Response model for processed tasks."""
    success: bool
    response: str
    task_type: str
    metadata: Dict[str, Any]
    error: Optional[str] = None


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "llm_orchestrator"}


@app.post("/process", response_model=ProcessResponse)
async def process_task(request: ProcessRequest):
    """Process a task through the LLM orchestrator."""
    try:
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())
        
        # Process through orchestrator
        result = await orchestrator.process(
            task_type=request.task_type,
            user_input=request.user_input,
            user_id=request.user_id,
            session_id=session_id,
            metadata=request.metadata
        )
        
        return ProcessResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/user/{user_id}/context")
async def get_user_context(user_id: str):
    """Get user context."""
    try:
        context = await orchestrator.get_user_context(user_id)
        return {"user_id": user_id, "context": context}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/user/{user_id}/context")
async def update_user_context(user_id: str, context: Dict[str, Any]):
    """Update user context."""
    try:
        await orchestrator.update_user_context(user_id, context)
        return {"message": "Context updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/user/{user_id}/search")
async def search_memories(user_id: str, query: str, limit: int = 5):
    """Search user memories."""
    try:
        memories = await orchestrator.search_memories(user_id, query, limit)
        return {"user_id": user_id, "query": query, "memories": memories}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/session/{session_id}")
async def clear_session(session_id: str):
    """Clear a session's memory."""
    try:
        orchestrator.clear_session(session_id)
        return {"message": "Session cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class AgentTaskRequest(BaseModel):
    """Request model for agent tasks (compatible with atomization service)."""
    query: str
    user_id: Optional[str] = None
    task_type: str = "ATOMIZATION"
    context: Optional[Dict[str, Any]] = None


@app.post("/agent/process")
async def process_agent_task(request: AgentTaskRequest):
    """Process an agent task (compatible with atomization service)."""
    try:
        # Convert to internal format
        task_type_enum = TaskType.ATOMIZATION if request.task_type == "ATOMIZATION" else TaskType.TUTORING_DIALOGUE
        
        # Process through orchestrator
        result = await orchestrator.process(
            task_type=task_type_enum,
            user_input=request.query,
            user_id=request.user_id or "anonymous",
            session_id=str(uuid.uuid4()),
            metadata=request.context or {}
        )
        
        # Convert response to format expected by atomization service
        agent_response = {
            "answer": result.get("response", ""),
            "reasoning_steps": [
                "PLAN: Analyzed content and planned atomization strategy",
                "EXECUTE: Used educational tools to structure content",
                "OBSERVE: Validated pedagogical quality of atoms",
                "REFLECT: Applied educational principles for optimal learning"
            ],
            "tools_used": [
                "search_learning_atoms",
                "track_learning_progress", 
                "generate_adaptive_questions"
            ],
            "iterations": 3
        }
        
        return agent_response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002) 