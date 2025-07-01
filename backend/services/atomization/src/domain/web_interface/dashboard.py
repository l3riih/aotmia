from __future__ import annotations

"""Web interface dashboard for atomization pipeline monitoring.

Provides real-time monitoring of the atomization process, including:
- File upload interface
- Processing progress tracking
- Results visualization
- Quality metrics display
- Dependency graph viewer
"""

from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates
from typing import Dict, Any, List, Optional
import structlog
import json
from pathlib import Path

logger = structlog.get_logger()
router = APIRouter()

# Templates directory (relative to this file)
templates_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))


@router.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request):
    """Main dashboard page for atomization pipeline."""
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "title": "Atomia - Pipeline de Atomización",
        "page": "dashboard"
    })


@router.get("/upload", response_class=HTMLResponse)
async def upload_interface(request: Request):
    """File upload interface."""
    return templates.TemplateResponse("upload.html", {
        "request": request,
        "title": "Subir Documento - Atomia",
        "page": "upload",
        "supported_formats": [
            {"ext": "PDF", "desc": "Documentos PDF"},
            {"ext": "DOCX", "desc": "Documentos Word"},
            {"ext": "TXT", "desc": "Archivos de texto plano"},
            {"ext": "HTML", "desc": "Páginas web"},
            {"ext": "MD", "desc": "Archivos Markdown"}
        ]
    })


@router.get("/monitor/{processing_id}", response_class=HTMLResponse)
async def monitor_processing(request: Request, processing_id: str):
    """Real-time monitoring of processing pipeline."""
    return templates.TemplateResponse("monitor.html", {
        "request": request,
        "title": f"Monitoreo - {processing_id}",
        "page": "monitor",
        "processing_id": processing_id
    })


@router.get("/results/{result_id}", response_class=HTMLResponse)
async def view_results(request: Request, result_id: str):
    """View atomization results with interactive visualizations."""
    
    # TODO: Fetch actual results from cache/database
    # For now, return mock data structure
    mock_results = {
        "result_id": result_id,
        "document_name": "ejemplo_documento.pdf",
        "processing_time": "2m 34s",
        "atoms_created": 15,
        "chunks_processed": 4,
        "quality_score": 0.87,
        "concepts_identified": ["funciones", "derivadas", "límites", "continuidad"],
        "atoms": [
            {
                "id": "atom_001",
                "title": "Introducción a las Funciones",
                "difficulty": "básico",
                "estimated_time": 10,
                "prerequisites": [],
                "quality_score": 0.92
            },
            {
                "id": "atom_002", 
                "title": "Tipos de Funciones",
                "difficulty": "intermedio",
                "estimated_time": 15,
                "prerequisites": ["atom_001"],
                "quality_score": 0.88
            }
        ]
    }
    
    return templates.TemplateResponse("results.html", {
        "request": request,
        "title": f"Resultados - {mock_results['document_name']}",
        "page": "results",
        "results": mock_results,
        "results_json": json.dumps(mock_results, indent=2)
    })


@router.get("/graph/{result_id}", response_class=HTMLResponse)
async def dependency_graph_viewer(request: Request, result_id: str):
    """Interactive dependency graph visualization."""
    
    # Mock graph data for visualization
    mock_graph = {
        "nodes": [
            {"id": "atom_001", "label": "Introducción a Funciones", "level": 1, "difficulty": "básico"},
            {"id": "atom_002", "label": "Tipos de Funciones", "level": 2, "difficulty": "intermedio"},
            {"id": "atom_003", "label": "Composición de Funciones", "level": 3, "difficulty": "avanzado"},
            {"id": "atom_004", "label": "Funciones Inversas", "level": 3, "difficulty": "avanzado"}
        ],
        "edges": [
            {"from": "atom_001", "to": "atom_002"},
            {"from": "atom_002", "to": "atom_003"},
            {"from": "atom_002", "to": "atom_004"}
        ]
    }
    
    return templates.TemplateResponse("graph.html", {
        "request": request,
        "title": "Grafo de Dependencias",
        "page": "graph",
        "graph_data": json.dumps(mock_graph),
        "result_id": result_id
    })


@router.get("/api/processing-status/{processing_id}")
async def get_processing_status_api(processing_id: str) -> Dict[str, Any]:
    """API endpoint for real-time processing status updates."""
    
    # TODO: Implement real status tracking
    # For now, return mock progression
    mock_status = {
        "processing_id": processing_id,
        "status": "processing",
        "current_step": "atomize",
        "progress_percentage": 65,
        "steps_completed": ["parse", "chunk"],
        "current_step_details": "Procesando chunk 3 de 4 con agente educativo",
        "estimated_time_remaining": "1m 15s",
        "atoms_created_so_far": 8,
        "chunks_processed": 3,
        "chunks_total": 4
    }
    
    return mock_status


@router.get("/api/results-summary/{result_id}")
async def get_results_summary_api(result_id: str) -> Dict[str, Any]:
    """API endpoint for results summary data."""
    
    # TODO: Fetch from actual storage
    mock_summary = {
        "result_id": result_id,
        "success": True,
        "atoms_count": 15,
        "quality_metrics": {
            "average_quality_score": 0.87,
            "validation_pass_rate": 0.93,
            "dependency_coherence": 0.91
        },
        "processing_metrics": {
            "total_time_seconds": 154,
            "chunks_processed": 4,
            "concepts_identified": 12,
            "cross_chunk_dependencies": 6
        },
        "file_info": {
            "original_filename": "documento_ejemplo.pdf",
            "size_mb": 2.3,
            "pages": 45
        }
    }
    
    return mock_summary


# Static files and assets
@router.get("/assets/{asset_type}/{filename}")
async def serve_assets(asset_type: str, filename: str):
    """Serve static assets (CSS, JS, images)."""
    
    # In production, this should be handled by nginx or similar
    # For development, we can serve basic assets
    
    assets_dir = Path(__file__).parent / "static" / asset_type
    file_path = assets_dir / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Asset not found")
    
    # Return appropriate content type based on file extension
    content_type = {
        ".css": "text/css",
        ".js": "application/javascript", 
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".svg": "image/svg+xml"
    }.get(file_path.suffix, "application/octet-stream")
    
    with open(file_path, "rb") as f:
        content = f.read()
    
    return Response(content=content, media_type=content_type) 