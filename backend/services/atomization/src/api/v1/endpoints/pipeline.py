"""
Pipeline endpoints para atomización de documentos completos
"""

from fastapi import APIRouter, BackgroundTasks, UploadFile, File, Form
from typing import Dict, Any
import structlog

from ....schemas import PipelineResponse

router = APIRouter()
logger = structlog.get_logger()


@router.post("/run", response_model=PipelineResponse)
async def run_pipeline(
    file: UploadFile = File(...),
    objectives: str = Form(""),
    difficulty: str = Form("intermedio"),
    user_id: str = Form(None),
    overlap_ratio: float = Form(0.1),
    background_tasks: BackgroundTasks = BackgroundTasks()
) -> PipelineResponse:
    """
    Run the complete atomization pipeline on an uploaded file.
    
    Supported formats: PDF, DOCX, TXT, HTML, MD, EPUB, URLs
    """
    try:
        # Read file content
        content = await file.read()
        
        logger.info(
            "Pipeline started",
            filename=file.filename,
            size=len(content),
            difficulty=difficulty,
            overlap_ratio=overlap_ratio
        )
        
        # Mock response for now
        mock_atoms = [
            {
                "id": "mock-atom-1",
                "title": f"Átomo procesado de {file.filename}",
                "content": f"Contenido atomizado con dificultad {difficulty}",
                "difficulty_level": difficulty,
                "prerequisites": [],
                "learning_objectives": [f"Aprender desde {file.filename}"],
                "estimated_time_minutes": 10,
                "tags": ["mock", "pipeline"]
            }
        ]
        
        mock_metrics = {
            "coherence": {"score": 0.85},
            "coverage": {"coverage_ratio": 0.92},
            "quality": 0.88
        }
        
        logger.info("Pipeline completed", filename=file.filename, atoms=len(mock_atoms))
        
        return PipelineResponse(
            success=True,
            atoms=mock_atoms,
            metadata={
                "filename": file.filename,
                "overlap_ratio": overlap_ratio,
                "processing_mode": "mock"
            },
            metrics=mock_metrics,
            metrics_report="Mock pipeline execution completed successfully"
        )
        
    except Exception as e:
        logger.error("Pipeline execution failed", error=str(e))
        return PipelineResponse(
            success=False,
            error=str(e),
            atoms=[],
            metadata={},
            metrics={}
        )


@router.get("/status")
async def get_pipeline_status():
    """Get pipeline status information."""
    return {
        "status": "operational",
        "supported_formats": ["PDF", "DOCX", "TXT", "HTML", "MD", "EPUB"],
        "pipeline_version": "1.0",
        "steps": ["parse", "chunk", "atomize", "relate", "validate", "store", "index", "metrics"]
    } 