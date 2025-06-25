"""
Endpoints para atomización agéntica de contenido educativo
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, UploadFile, File
from typing import List, Optional
import structlog
from io import BytesIO
from pypdf import PdfReader

from ....schemas import (
    AtomizationRequest,
    AgenticAtomizationResponse,
    LearningAtomRead
)
from ....domain.services.agentic_atomization_service import AgenticAtomizationService
from ....core.dependencies import get_agentic_atomization_service
from ....core.logging import log_agentic_operation

logger = structlog.get_logger()
router = APIRouter()


@router.post("/atomize", response_model=AgenticAtomizationResponse)
async def atomize_content_agentic(
    request: AtomizationRequest,
    background_tasks: BackgroundTasks,
    service: AgenticAtomizationService = Depends(get_agentic_atomization_service)
) -> AgenticAtomizationResponse:
    """
    Atomiza contenido educativo usando el agente de IA con capacidades de razonamiento.
    
    El agente ejecuta el workflow Plan-Execute-Observe-Reflect:
    1. **PLAN**: Analiza el contenido y planifica estrategia de atomización
    2. **EXECUTE**: Usa herramientas educativas especializadas  
    3. **OBSERVE**: Valida la calidad pedagógica de los átomos
    4. **REFLECT**: Mejora los átomos basado en principios educativos
    
    **Parámetros:**
    - **content**: Texto del material educativo a atomizar
    - **objectives**: Objetivos de aprendizaje del curso (opcional)
    - **difficulty_level**: Nivel de dificultad (básico, intermedio, avanzado)
    - **user_id**: ID del usuario para contexto personalizado
    - **context**: Información adicional de contexto
    
    **Retorna:**
    - Lista de átomos de aprendizaje creados
    - Metadatos del proceso agéntico (pasos de razonamiento, herramientas usadas)
    - Métricas de calidad del razonamiento
    """
    try:
        log_agentic_operation(
            logger,
            "atomization_start",
            user_id=request.user_id,
            content_length=len(request.content),
            difficulty=request.difficulty_level
        )
        
        # Llamar al servicio agéntico
        atoms = await service.atomize_with_agent(
            content=request.content,
            objectives=request.objectives or "",
            difficulty=request.difficulty_level,
            user_id=request.user_id
        )
        
        # Obtener metadatos del proceso agéntico
        agent_metadata = getattr(atoms, 'agent_metadata', {})
        reasoning_steps = agent_metadata.get('reasoning_steps', [])
        tools_used = agent_metadata.get('tools_used', [])
        iterations = agent_metadata.get('iterations', 0)
        quality_score = agent_metadata.get('quality_score', 0.0)
        
        log_agentic_operation(
            logger,
            "atomization_complete",
            user_id=request.user_id,
            atoms_created=len(atoms),
            reasoning_steps=len(reasoning_steps),
            tools_used=len(tools_used),
            iterations=iterations,
            quality_score=quality_score
        )
        
        # Programar tareas en background (analytics, notificaciones, etc.)
        background_tasks.add_task(
            _process_atomization_analytics,
            user_id=request.user_id,
            atoms_count=len(atoms),
            quality_score=quality_score
        )
        
        return AgenticAtomizationResponse(
            atoms=atoms,
            agent_metadata=agent_metadata,
            reasoning_steps=reasoning_steps,
            tools_used=tools_used,
            iterations=iterations,
            quality_score=quality_score
        )
        
    except Exception as e:
        logger.error(
            "Atomization error",
            error=str(e),
            user_id=request.user_id,
            content_length=len(request.content) if request.content else 0
        )
        raise HTTPException(
            status_code=500,
            detail=f"Error en atomización agéntica: {str(e)}"
        )


@router.post("/atomize-file", response_model=AgenticAtomizationResponse)
async def atomize_file_agentic(
    file: UploadFile = File(...),
    objectives: Optional[str] = None,
    difficulty_level: str = "intermedio",
    user_id: Optional[str] = None,
    service: AgenticAtomizationService = Depends(get_agentic_atomization_service)
) -> AgenticAtomizationResponse:
    """
    Atomiza contenido desde un archivo (PDF, TXT, DOCX) usando capacidades agénticas.
    
    Extrae el contenido del archivo y aplica el mismo proceso de atomización agéntica.
    """
    try:
        # Extraer contenido del archivo
        content = await _extract_content_from_file(file)
        
        if not content.strip():
            raise HTTPException(
                status_code=400,
                detail="No se pudo extraer contenido válido del archivo"
            )
        
        # Crear request de atomización
        request = AtomizationRequest(
            content=content,
            objectives=objectives,
            difficulty_level=difficulty_level,
            user_id=user_id,
            context={"source": "file", "filename": file.filename}
        )
        
        # Reutilizar el endpoint de atomización
        return await atomize_content_agentic(request, BackgroundTasks(), service)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "File atomization error",
            error=str(e),
            filename=file.filename,
            user_id=user_id
        )
        raise HTTPException(
            status_code=500,
            detail=f"Error procesando archivo: {str(e)}"
        )


@router.get("/atoms/{atom_id}", response_model=LearningAtomRead)
async def get_atom(
    atom_id: str,
    service: AgenticAtomizationService = Depends(get_agentic_atomization_service)
) -> LearningAtomRead:
    """Obtiene un átomo de aprendizaje por ID"""
    try:
        atom = await service.get_atom_by_id(atom_id)
        if not atom:
            raise HTTPException(
                status_code=404,
                detail=f"Átomo {atom_id} no encontrado"
            )
        return atom
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Get atom error", error=str(e), atom_id=atom_id)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/atoms/{atom_id}", response_model=LearningAtomRead)
async def update_atom(
    atom_id: str,
    updates: dict,
    service: AgenticAtomizationService = Depends(get_agentic_atomization_service)
) -> LearningAtomRead:
    """Actualiza un átomo de aprendizaje existente"""
    try:
        atom = await service.update_atom(atom_id, updates)
        if not atom:
            raise HTTPException(
                status_code=404,
                detail=f"Átomo {atom_id} no encontrado"
            )
        
        log_agentic_operation(
            logger,
            "atom_updated",
            atom_id=atom_id,
            updates=list(updates.keys())
        )
        
        return atom
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Update atom error", error=str(e), atom_id=atom_id)
        raise HTTPException(status_code=500, detail=str(e))


async def _extract_content_from_file(file: UploadFile) -> str:
    """Extrae contenido de texto de diferentes tipos de archivo"""
    content = ""
    
    if file.content_type == "text/plain":
        content_bytes = await file.read()
        content = content_bytes.decode("utf-8")
    elif file.content_type == "application/pdf":
        try:
            content_bytes = await file.read()
            pdf_file = BytesIO(content_bytes)
            reader = PdfReader(pdf_file)
            text_parts = [page.extract_text() for page in reader.pages]
            content = "\n".join(filter(None, text_parts))
        except Exception as e:
            logger.error("PDF extraction failed", filename=file.filename, error=str(e))
            raise HTTPException(
                status_code=400,
                detail=f"No se pudo procesar el archivo PDF: {str(e)}"
            )
    elif file.content_type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
        # TODO: Implementar extracción de DOCX
        raise HTTPException(
            status_code=400,
            detail="Extracción de DOCX no implementada aún"
        )
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo de archivo no soportado: {file.content_type}"
        )
    
    return content


async def _process_atomization_analytics(
    user_id: Optional[str],
    atoms_count: int,
    quality_score: float
) -> None:
    """Procesa analytics de atomización en background"""
    try:
        # TODO: Implementar analytics y métricas
        logger.info(
            "Processing atomization analytics",
            user_id=user_id,
            atoms_count=atoms_count,
            quality_score=quality_score
        )
    except Exception as e:
        logger.error("Analytics processing error", error=str(e)) 